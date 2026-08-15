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
    /// bookkeeping is the client's job). Re-shaped by A1 (2026-08-04): the
    /// reputation snapshot, the directive/reputation callbacks, and the
    /// recent-actions block left with the behavior/reputation removal.
    ///
    /// Scene state frozen within a scene: the identity version and the
    /// scene basis move only at scene boundaries (or session start). The
    /// loaded set + damper streak and the scene context fields are
    /// caller-held and reset at boundaries. AsOf is the session's
    /// time-travel surface: it rides retrieval's age computation AND
    /// becomes the client timestamp of observes and corrections.
    /// </summary>
    public sealed class NpcSession
    {
        private readonly NpcMemoryClient _client;
        private readonly string _phaseTag;

        public Guid AgentId { get; }
        public string? IdentityVersion { get; private set; }
        public DateTimeOffset? SceneStartedAt { get; private set; }
        public DateTimeOffset? AsOf { get; set; }
        public List<Guid>? LoadedMemoryIds { get; private set; }
        public int GateFruitlessStreak { get; private set; }
        public string? ContextLocation { get; set; }
        public List<string>? ContextEntities { get; set; }
        public DateTimeOffset? ContextEventTime { get; set; }

        /// <summary>Mirrors the Python runner's `debug` flag on every turn
        /// request (app\session.py) — the server widens its debug payload.</summary>
        public bool Debug { get; set; }

        public NpcSession(
            NpcMemoryClient client,
            Guid agentId,
            string phaseTag = "unity")
        {
            _client = client;
            AgentId = agentId;
            _phaseTag = phaseTag;
        }

        private DateTimeOffset Now() => AsOf ?? DateTimeOffset.UtcNow;

        private DialogueTurnRequest BuildTurnRequest(
            string text,
            int? k,
            WeightOverrides? weightOverrides) =>
            new DialogueTurnRequest
            {
                AgentId = AgentId,
                Utterance = text,
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
                Debug = Debug,
            };

        /// <summary>One dialogue turn, drained (POST /v1/dialogue/turn).
        /// `weightOverrides` is the weights-on-speech slot (A1 re-shape):
        /// per-call multipliers re-rank the served view feeding the prose
        /// prompt; the result's DialogueView reports that ranking.</summary>
        public async Task<DialogueTurnResult> SayAsync(
            string text,
            int? k = null,
            WeightOverrides? weightOverrides = null,
            CancellationToken ct = default)
        {
            var result = await _client
                .DialogueTurnAsync(BuildTurnRequest(text, k, weightOverrides), ct);
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
            int? k = null,
            WeightOverrides? weightOverrides = null,
            CancellationToken ct = default)
        {
            var result = await _client
                .DialogueTurnStreamAsync(
                    BuildTurnRequest(text, k, weightOverrides),
                    onChunk,
                    onReconstructing,
                    ct);
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
        /// the identity document server-side), then refresh the frozen scene
        /// state — within the ending scene none of it moved.</summary>
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
                    ct);
            IdentityVersion = result.IdentityVersion;
            SceneStartedAt = Now();
            LoadedMemoryIds = null; // next turn is a loader
            GateFruitlessStreak = 0; // the damper dies with the scene
            ContextLocation = null; // a new scene is a new place/cast
            ContextEntities = null;
            ContextEventTime = null;
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

        /// <summary>The reflect verb at the session's effective time
        /// (reflection.md, 2026-08-15; the CorrectAsync time precedent).
        /// Deliberately does NOT touch the frozen scene state:
        /// IdentityVersion stays caller-frozen until the next scene boundary
        /// picks up the recompiled document — reflect at scene edges and the
        /// trim-eviction exposure window vanishes.</summary>
        public Task<ReflectResult> ReflectAsync(
            bool? consolidate = null, CancellationToken ct = default) =>
            _client.ReflectAsync(
                AgentId,
                new ReflectRequest
                {
                    ClientTimestamp = Now(),
                    Consolidate = consolidate,
                },
                ct);

        public Task<PinResult> PinAsync(
            Guid memoryId, bool pinned, CancellationToken ct = default) =>
            _client.SetPinAsync(memoryId, pinned, ct);
    }
}
