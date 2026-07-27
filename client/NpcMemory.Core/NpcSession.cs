using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace NpcMemory
{
    /// <summary>
    /// One NPC session: the caller-held scene state + turn bookkeeping —
    /// the field-for-field port of the Python session runner
    /// (app\session.py; the server is STATELESS by ruling, so this
    /// bookkeeping is the client's job).
    ///
    /// Scene state frozen within a scene: the reputation snapshot, the
    /// identity version, and the scene basis move only at scene boundaries
    /// (or session start). The loaded set + damper streak, the scene
    /// context fields, and the recent-actions block are caller-held and
    /// reset at boundaries. AsOf is the session's time-travel surface: it
    /// rides retrieval's age computation AND becomes the client timestamp
    /// of observes and corrections.
    ///
    /// The reputation snapshot over HTTP: the Python runner re-reads
    /// agents.reputation at each boundary; no HTTP agent-state read exists,
    /// so this port refreshes the snapshot from the last turn's
    /// reputation_after (identical for a single-client session — the row
    /// value IS the last apply's result). A multi-client integration would
    /// want an agent-state read route; surfaced in unity-client.md.
    /// </summary>
    public sealed class NpcSession
    {
        private readonly NpcMemoryClient _client;
        private readonly string _phaseTag;
        private readonly int _recentActionsCap;
        private double? _lastReputationAfter;

        public Guid AgentId { get; }
        public double ReputationSnapshot { get; private set; }
        public string? IdentityVersion { get; private set; }
        public DateTimeOffset? SceneStartedAt { get; private set; }
        public DateTimeOffset? AsOf { get; set; }
        public List<Guid>? LoadedMemoryIds { get; private set; }
        public int GateFruitlessStreak { get; private set; }
        public string? ContextLocation { get; set; }
        public List<string>? ContextEntities { get; set; }
        public DateTimeOffset? ContextEventTime { get; set; }
        public List<RecentAction> RecentActions { get; } = new List<RecentAction>();

        /// <summary>Fires when a turn resolves a directive (never on dropped).</summary>
        public event Action<ActionDirective>? OnDirective;

        /// <summary>Fires after every turn's reputation apply: (prev, after).</summary>
        public event Action<double, double>? OnReputationChanged;

        /// <summary>
        /// recentActionsCap mirrors the server's per-agent
        /// `recent_actions_cap` knob — the server value is authoritative;
        /// pass the same number here (the service default is 8 unless the
        /// agent config overrides it).
        /// </summary>
        public NpcSession(
            NpcMemoryClient client,
            Guid agentId,
            double initialReputationSnapshot,
            string phaseTag = "unity",
            int recentActionsCap = 8)
        {
            _client = client;
            AgentId = agentId;
            ReputationSnapshot = initialReputationSnapshot;
            _phaseTag = phaseTag;
            _recentActionsCap = recentActionsCap;
        }

        private DateTimeOffset Now() => AsOf ?? DateTimeOffset.UtcNow;

        private DialogueTurnRequest BuildTurnRequest(
            string text,
            double? reputationDeltaOverride,
            List<string>? actionVocabulary,
            int? k,
            WeightOverrides? weightOverrides) =>
            new DialogueTurnRequest
            {
                AgentId = AgentId,
                Utterance = text,
                ReputationSnapshot = ReputationSnapshot,
                ReputationDeltaOverride = reputationDeltaOverride,
                ActionVocabulary = actionVocabulary,
                K = k,
                AsOf = AsOf,
                LocationName = ContextLocation,
                Entities = ContextEntities,
                EventTime = ContextEventTime,
                IdentityVersion = IdentityVersion,
                SceneStartedAt = SceneStartedAt,
                LoadedMemoryIds = LoadedMemoryIds,
                GateFruitlessStreak = GateFruitlessStreak,
                WeightOverrides = weightOverrides,
                RecentActions = new List<RecentAction>(RecentActions),
            };

        /// <summary>One dialogue turn, drained (POST /v1/dialogue/turn).</summary>
        public async Task<DialogueTurnResult> SayAsync(
            string text,
            double? reputationDeltaOverride = null,
            List<string>? actionVocabulary = null,
            int? k = null,
            WeightOverrides? weightOverrides = null,
            CancellationToken ct = default)
        {
            var result = await _client
                .DialogueTurnAsync(
                    BuildTurnRequest(
                        text, reputationDeltaOverride, actionVocabulary, k, weightOverrides),
                    ct)
                .ConfigureAwait(false);
            ApplyTurnResult(result);
            return result;
        }

        /// <summary>One streaming dialogue turn (the SSE route): onChunk per
        /// prose chunk; onReconstructing during a blocking mid-scene
        /// retelling — the "(reconstructing…)" hook.</summary>
        public async Task<DialogueTurnResult> SayStreamAsync(
            string text,
            Action<string> onChunk,
            Action? onReconstructing = null,
            double? reputationDeltaOverride = null,
            List<string>? actionVocabulary = null,
            int? k = null,
            WeightOverrides? weightOverrides = null,
            CancellationToken ct = default)
        {
            var result = await _client
                .DialogueTurnStreamAsync(
                    BuildTurnRequest(
                        text, reputationDeltaOverride, actionVocabulary, k, weightOverrides),
                    onChunk,
                    onReconstructing,
                    ct)
                .ConfigureAwait(false);
            ApplyTurnResult(result);
            return result;
        }

        /// <summary>Post-turn scene-state bookkeeping, in ONE place so the
        /// streaming and drained paths cannot drift (the Python
        /// _apply_turn_result, ported). Keyed on what the SERVER reports
        /// (gate.evaluated / fired), not on what was sent.</summary>
        private void ApplyTurnResult(DialogueTurnResult result)
        {
            var gate = result.Instrumentation.Retrieval.Gate;
            if (!gate.Evaluated)
            {
                // Loader turn: the served IDs become the scene's loaded set.
                LoadedMemoryIds = result.Items.Select(i => i.MemoryId).ToList();
                GateFruitlessStreak = 0;
            }
            else if (gate.Fired)
            {
                // Gated fire: this turn's gate-fetched IDs append; the streak
                // resets on a productive fetch, increments on a fruitless one.
                LoadedMemoryIds = (LoadedMemoryIds ?? new List<Guid>())
                    .Concat(
                        result.Items.Where(i => i.GateFetched).Select(i => i.MemoryId))
                    .ToList();
                GateFruitlessStreak =
                    gate.FetchedNewCount == 0 ? GateFruitlessStreak + 1 : 0;
            }
            // Gated-closed: untouched.

            if (result.Directive != null)
            {
                // Only what actually happened enters the record (a dropped
                // directive appends nothing), capped.
                RecentActions.Add(new RecentAction
                {
                    Type = result.Directive.Type,
                    Params = result.Directive.Params,
                    At = Now(),
                });
                if (RecentActions.Count > _recentActionsCap)
                {
                    RecentActions.RemoveRange(0, RecentActions.Count - _recentActionsCap);
                }
                OnDirective?.Invoke(result.Directive);
            }

            _lastReputationAfter = result.ReputationAfter;
            OnReputationChanged?.Invoke(result.ReputationPrev, result.ReputationAfter);
        }

        /// <summary>One observe event at the session's effective time.</summary>
        public Task<IngestResult> ObserveAsync(
            string text, CancellationToken ct = default) =>
            _client.ObserveAsync(
                new ObserveEvent
                {
                    AgentId = AgentId,
                    ObservationText = text,
                    PhaseTag = _phaseTag,
                    ClientTimestamp = Now(),
                    Provenance = "lived",
                },
                ct);

        /// <summary>Scene boundary: emit the event (the handler recompiles
        /// the identity document server-side), then refresh every piece of
        /// frozen scene state — within the ending scene none of it moved.</summary>
        public async Task<SceneResult> SceneBoundaryAsync(
            string? sceneType = null, CancellationToken ct = default)
        {
            var result = await _client
                .SceneBoundaryAsync(
                    new SceneBoundaryEvent
                    {
                        AgentId = AgentId,
                        ClientTimestamp = Now(),
                        SceneType = sceneType,
                    },
                    ct)
                .ConfigureAwait(false);
            if (_lastReputationAfter is double after)
            {
                ReputationSnapshot = after; // the row value == the last apply
            }
            IdentityVersion = result.IdentityVersion;
            SceneStartedAt = Now();
            LoadedMemoryIds = null; // next turn is a loader
            GateFruitlessStreak = 0; // the damper dies with the scene
            ContextLocation = null; // a new scene is a new place/cast
            ContextEntities = null;
            ContextEventTime = null;
            RecentActions.Clear(); // no world-fact action history carries over
            return result;
        }

        /// <summary>Authorial correction at the session's effective time.</summary>
        public Task<CorrectionResult> CorrectAsync(
            Guid memoryId,
            string content,
            Guid? expectedDetailId = null,
            List<string>? entities = null,
            CancellationToken ct = default) =>
            _client.CorrectAsync(
                memoryId,
                new CorrectionRequest
                {
                    Content = content,
                    ClientTimestamp = Now(),
                    ExpectedDetailId = expectedDetailId,
                    Entities = entities,
                },
                ct);

        public Task<PinResult> PinAsync(
            Guid memoryId, bool pinned, CancellationToken ct = default) =>
            _client.SetPinAsync(memoryId, pinned, ct);
    }
}
