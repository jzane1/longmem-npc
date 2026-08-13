using System;
using System.Collections.Generic;
using Newtonsoft.Json.Linq;

namespace NpcMemory
{
    // ------------------------------------------------------------------
    // Wire models — a field-for-field mirror of app\schemas.py (the route
    // contract is pass-through, so these are both the request and response
    // shapes). Property names map to snake_case via NpcJson's naming
    // strategy. Optional service fields are nullable here; nullable LISTS
    // are deliberate — see NpcJson on the null-vs-absent contract.
    // ------------------------------------------------------------------

    // -- events + operator verbs ---------------------------------------

    public sealed class AffectOverride
    {
        public double? Valence { get; set; }
        public double? Arousal { get; set; }
        public JObject? Detail { get; set; }
    }

    public sealed class ObserveEvent
    {
        public Guid AgentId { get; set; }
        public string ObservationText { get; set; } = "";
        public string PhaseTag { get; set; } = "";
        public DateTimeOffset ClientTimestamp { get; set; }
        public string Provenance { get; set; } = "lived";
        public string? Typology { get; set; }
        public double? TypologyConfidence { get; set; }
        public string? DecayClass { get; set; }
        public string? LocationName { get; set; }
        public string? LocationDescription { get; set; }
        public List<string>? Entities { get; set; }
        public DateTimeOffset? EventTime { get; set; }
        public AffectOverride? Affect { get; set; }
        public bool Pinned { get; set; }
        public string? EventId { get; set; }
    }

    public sealed class SceneBoundaryEvent
    {
        public Guid AgentId { get; set; }
        public DateTimeOffset ClientTimestamp { get; set; }
        public string? SceneType { get; set; }
        public string? EventId { get; set; }
    }

    public sealed class PinRequest
    {
        public bool Pinned { get; set; }
    }

    public sealed class CorrectionRequest
    {
        public string Content { get; set; } = "";
        public DateTimeOffset ClientTimestamp { get; set; }
        public Guid? ExpectedDetailId { get; set; }
        public List<string>? Entities { get; set; }
    }

    public sealed class CreateAgentRequest
    {
        public string Name { get; set; } = "";
        public string? SeedIdentity { get; set; }
        public double? Rigidity { get; set; }
        public string? DiagnosticityGoal { get; set; }
        public JObject? Config { get; set; }
    }

    // -- event results --------------------------------------------------

    public sealed class AffectOut
    {
        public double? Valence { get; set; }
        public double? Arousal { get; set; }
        public JObject? Detail { get; set; }
    }

    public sealed class Instrumentation
    {
        public double NlpMs { get; set; }
        public double EmbedMs { get; set; }
        public double HaikuMs { get; set; }
        public double InsertMs { get; set; }
        public double TotalMs { get; set; }
        public int HaikuInputTokens { get; set; }
        public int HaikuOutputTokens { get; set; }
        public int EmbeddingTokens { get; set; }
        public bool Escalated { get; set; }
        public List<string> EscalatedBy { get; set; } = new List<string>();
        public double EscalationMs { get; set; }
        public int EscalationInputTokens { get; set; }
        public int EscalationOutputTokens { get; set; }
    }

    public sealed class IngestResult
    {
        public Guid MemoryId { get; set; }
        public Guid DetailId { get; set; }
        public Guid FactVersionId { get; set; }
        public List<Guid> GistSpanIds { get; set; } = new List<Guid>();
        public List<Guid> NewComponentIds { get; set; } = new List<Guid>();
        // Nullable since the deferred-write build (2026-08-12): a
        // deferred-mode observe returns the write-call scalars as null with
        // EnrichmentPending true — the worker fills them server-side later.
        public double? ImportanceRaw { get; set; }
        public string? Typology { get; set; }
        public double? TypologyConfidence { get; set; }
        public string? TypologySource { get; set; }
        public string Provenance { get; set; } = "";
        public AffectOut Affect { get; set; } = new AffectOut();
        public List<string> Entities { get; set; } = new List<string>();
        public string DecayClass { get; set; } = "";
        public bool DecayClassUnknown { get; set; }
        public bool ScoringFailed { get; set; }
        public bool EscalationFailed { get; set; }
        public bool EmbeddingFailed { get; set; }
        public bool Pinned { get; set; }
        public bool EnrichmentPending { get; set; }
        public Instrumentation Instrumentation { get; set; } = new Instrumentation();
    }

    public sealed class SceneResult
    {
        public Guid AgentId { get; set; }
        public bool Accepted { get; set; }
        public double TotalMs { get; set; }
        public string? IdentityVersion { get; set; }
        public bool IdentityDocumentNew { get; set; }
    }

    public sealed class PinResult
    {
        public Guid MemoryId { get; set; }
        public bool Pinned { get; set; }
        public double TotalMs { get; set; }
    }

    public sealed class CorrectionResult
    {
        public Guid MemoryId { get; set; }
        public Guid DetailId { get; set; }
        public Guid SupersededDetailId { get; set; }
        public Guid FactVersionId { get; set; }
        public Guid SupersededFactVersionId { get; set; }
        public int EvictedCacheRows { get; set; }
        public List<string> Entities { get; set; } = new List<string>();
        public double EmbedMs { get; set; }
        public int EmbeddingTokens { get; set; }
        public double NlpMs { get; set; }
        public double TotalMs { get; set; }
    }

    public sealed class CreateAgentResult
    {
        public Guid AgentId { get; set; }
        public string Name { get; set; } = "";
        public string? SeedIdentity { get; set; }
        public double? Rigidity { get; set; }
        public string? DiagnosticityGoal { get; set; }
        public JObject Config { get; set; } = new JObject();
        public double TotalMs { get; set; }
    }

    // -- read path ------------------------------------------------------

    public sealed class WeightOverrides
    {
        public double? Relevance { get; set; }
        public double? Recency { get; set; }
        public double? Importance { get; set; }
    }

    public sealed class DialogueInitRequest
    {
        public Guid AgentId { get; set; }
        public string QueryText { get; set; } = "";
        public int? K { get; set; }
        public string? LocationName { get; set; }
        public List<string>? Entities { get; set; }
        public DateTimeOffset? EventTime { get; set; }
        public DateTimeOffset? AsOf { get; set; }
        public string? IdentityVersion { get; set; }
        public DateTimeOffset? SceneStartedAt { get; set; }
        public List<Guid>? LoadedMemoryIds { get; set; }
        public int GateFruitlessStreak { get; set; }
    }

    public sealed class RetrievedMemory
    {
        public Guid MemoryId { get; set; }
        public Guid DetailId { get; set; }
        public string Content { get; set; } = "";
        public string ReadMode { get; set; } = "";
        public bool Pinned { get; set; }
        public double Score { get; set; }
        public double? Relevance { get; set; }
        public double Recency { get; set; }
        public double ImportanceNorm { get; set; }
        public double ImportanceRaw { get; set; }
        public bool GateFetched { get; set; }
    }

    public sealed class GateInstrumentation
    {
        public bool Evaluated { get; set; }
        public bool Fired { get; set; }
        public List<string> SignalsFired { get; set; } = new List<string>();
        public string? DegradedRung { get; set; }
        public double? NoveltyMinDistance { get; set; }
        public int NullEmbeddingLoadedCount { get; set; }
        public int LoadedMissingCount { get; set; }
        public List<string> UncoveredEntities { get; set; } = new List<string>();
        public List<Guid> FetchedMemoryIds { get; set; } = new List<Guid>();
        public int FetchedNewCount { get; set; }
        public bool Fruitless { get; set; }
        public bool DamperActive { get; set; }
        public bool? NoveltyOutscored { get; set; }
        public bool? EntityCovered { get; set; }
        public double GateMs { get; set; }
        public bool ReconstructingBlocked { get; set; }
    }

    public sealed class RetrievalInstrumentation
    {
        public double EmbedMs { get; set; }
        public double SqlMs { get; set; }
        public double ScoreMs { get; set; }
        public double TotalMs { get; set; }
        public int EmbeddingTokens { get; set; }
        public int CandidateCount { get; set; }
        public int KEffective { get; set; }
        public double LexicalSqlMs { get; set; }
        public int LexicalCandidateCount { get; set; }
        public bool Degraded { get; set; }
        public string? DegradedReason { get; set; }
        public DateTimeOffset AsOfEffective { get; set; }
        public bool ContextActive { get; set; }
        public List<string> ContextComponents { get; set; } = new List<string>();
        public double ReconstructionMs { get; set; }
        public int ReconstructionInputTokens { get; set; }
        public int ReconstructionOutputTokens { get; set; }
        public int ReconstructionEmbedTokens { get; set; }
        public int CacheHits { get; set; }
        public int CacheMisses { get; set; }
        public int WriteBacks { get; set; }
        public int DriftRefusals { get; set; }
        public string? IdentityVersionEffective { get; set; }
        public bool IdentityBootstrapped { get; set; }
        public GateInstrumentation Gate { get; set; } = new GateInstrumentation();
    }

    public sealed class RetrievalResult
    {
        public List<RetrievedMemory> Items { get; set; } = new List<RetrievedMemory>();
        public RetrievalInstrumentation Instrumentation { get; set; } =
            new RetrievalInstrumentation();
    }

    // -- dialogue turn --------------------------------------------------

    /// <summary>One (memory_id, score) tuple in the weight-ranked view that
    /// fed the prose prompt (weights-on-speech, A1 re-shape 2026-08-04).
    /// On a loader turn at default weights DialogueView equals the
    /// (id, score) projection of Items — the parity contract; on gated
    /// turns Items keeps the loaded+fetched serve shape while DialogueView
    /// is the global weight ranking.</summary>
    public sealed class ScoredRef
    {
        public Guid MemoryId { get; set; }
        public double Score { get; set; }
    }

    public sealed class DialogueTurnRequest
    {
        public Guid AgentId { get; set; }
        public string Utterance { get; set; } = "";
        public int? K { get; set; }
        public DateTimeOffset? AsOf { get; set; }
        public string? LocationName { get; set; }
        public List<string>? Entities { get; set; }
        public DateTimeOffset? EventTime { get; set; }
        public string? IdentityVersion { get; set; }
        public DateTimeOffset? SceneStartedAt { get; set; }

        /// <summary>null = LOADER TURN; an empty list = an empty loaded set
        /// the gate still evaluates. Never collapse one into the other.</summary>
        public List<Guid>? LoadedMemoryIds { get; set; }

        public int GateFruitlessStreak { get; set; }
        public WeightOverrides? WeightOverrides { get; set; }
        public bool Debug { get; set; }
    }

    public sealed class DialogueTurnInstrumentation
    {
        public RetrievalInstrumentation Retrieval { get; set; } =
            new RetrievalInstrumentation();
        public double SonnetMs { get; set; }
        public double SonnetFirstTokenMs { get; set; }
        public double TotalMs { get; set; }
        public int SonnetInputTokens { get; set; }
        public int SonnetOutputTokens { get; set; }
        public double? CostUsd { get; set; }
        public bool Degraded { get; set; }
        public string? DegradedReason { get; set; }
        public double FirstWordMs { get; set; }
        public double ProseStreamMs { get; set; }
        public double PerceivedFirstWordMs { get; set; }
    }

    public sealed class DialogueTurnResult
    {
        public Guid AgentId { get; set; }
        public string Content { get; set; } = "";
        public List<RetrievedMemory> Items { get; set; } = new List<RetrievedMemory>();
        public List<ScoredRef> DialogueView { get; set; } = new List<ScoredRef>();
        public DialogueTurnInstrumentation Instrumentation { get; set; } =
            new DialogueTurnInstrumentation();
    }

    // -- inspector reads (The Ledger's data source) ---------------------

    public sealed class DetailVersionOut
    {
        public Guid DetailId { get; set; }
        public string Content { get; set; } = "";
        public string? WriteCause { get; set; }
        public DateTimeOffset CreatedAt { get; set; }
        public DateTimeOffset ValidAt { get; set; }
        public DateTimeOffset? InvalidAt { get; set; }
        public bool IsLive { get; set; }
    }

    public sealed class FactVersionOut
    {
        public Guid FactVersionId { get; set; }
        public string BasisText { get; set; } = "";
        public string? WriteCause { get; set; }
        public DateTimeOffset CreatedAt { get; set; }
        public DateTimeOffset ValidAt { get; set; }
        public DateTimeOffset? InvalidAt { get; set; }
        public bool IsLive { get; set; }
        public bool HasEmbedding { get; set; }
        public List<string> Entities { get; set; } = new List<string>();
    }

    public sealed class GistSpanOut
    {
        public Guid SpanId { get; set; }
        public int StartChar { get; set; }
        public int EndChar { get; set; }
        public string? MatchedCategory { get; set; }
    }

    public sealed class EnrichmentRunOut
    {
        public int Attempt { get; set; }
        public string Outcome { get; set; } = "";
        public string? Error { get; set; }
        public List<string> Triggers { get; set; } = new List<string>();
        public bool EscalationFailed { get; set; }
        public bool EmbeddingRepaired { get; set; }
        public double? WriteMs { get; set; }
        public double? EscalationMs { get; set; }
        public double? EmbedMs { get; set; }
        public double? InsertMs { get; set; }
        public double? TotalMs { get; set; }
        public int WriteInputTokens { get; set; }
        public int WriteOutputTokens { get; set; }
        public int EscalationInputTokens { get; set; }
        public int EscalationOutputTokens { get; set; }
        public int EmbeddingTokens { get; set; }
        public DateTimeOffset CreatedAt { get; set; }
    }

    public sealed class MemoryChainResult
    {
        public Guid MemoryId { get; set; }
        public Guid AgentId { get; set; }
        public string ObservationText { get; set; } = "";
        public string Provenance { get; set; } = "";
        public string? Typology { get; set; }
        public string? DecayClass { get; set; }
        public bool Pinned { get; set; }
        public bool ScoringFailed { get; set; }
        public bool EscalationFailed { get; set; }
        public bool DecayClassUnknown { get; set; }
        public DateTimeOffset CreatedAt { get; set; }
        public DateTimeOffset ValidAt { get; set; }
        public DateTimeOffset? InvalidAt { get; set; }
        public string? LocationName { get; set; }
        public DateTimeOffset? EventTime { get; set; }
        public bool EnrichmentPending { get; set; }
        public int EnrichmentAttempts { get; set; }
        public List<EnrichmentRunOut> EnrichmentRuns { get; set; } = new List<EnrichmentRunOut>();
        public List<DetailVersionOut> Details { get; set; } = new List<DetailVersionOut>();
        public List<FactVersionOut> Facts { get; set; } = new List<FactVersionOut>();
        public List<GistSpanOut> GistSpans { get; set; } = new List<GistSpanOut>();
        public double TotalMs { get; set; }
    }

    public sealed class MemorySummaryOut
    {
        public Guid MemoryId { get; set; }
        public string ObservationText { get; set; } = "";
        public string? LiveContent { get; set; }
        public string? LiveWriteCause { get; set; }
        public int DetailCount { get; set; }
        public bool Pinned { get; set; }
        public DateTimeOffset ValidAt { get; set; }
        public DateTimeOffset? InvalidAt { get; set; }
    }

    public sealed class AgentMemoriesResult
    {
        public Guid AgentId { get; set; }
        public List<MemorySummaryOut> Memories { get; set; } = new List<MemorySummaryOut>();
        public int TotalCount { get; set; }
        public int Limit { get; set; }
        public double TotalMs { get; set; }
    }

    public sealed class ReconstructionMetricsResult
    {
        public Guid MemoryId { get; set; }
        public Guid AgentId { get; set; }
        public Guid? LiveDetailId { get; set; }
        public string? LiveWriteCause { get; set; }
        public string? AnchorCause { get; set; }
        public int GistFactsTotal { get; set; }
        public int GistFactsPresent { get; set; }
        public double? GistPrecision { get; set; }
        public int DetailLemmasTotal { get; set; }
        public int DetailLemmasPresent { get; set; }
        public double? DetailRecall { get; set; }
        public List<string> TellingEntities { get; set; } = new List<string>();
        public List<string> FabricatedEntities { get; set; } = new List<string>();
        public double? FabricationRate { get; set; }
        public double? KeywordRetention { get; set; }
        public List<int> CacheBands { get; set; } = new List<int>();
        public double MetricsMs { get; set; }
        public double TotalMs { get; set; }
    }
}
