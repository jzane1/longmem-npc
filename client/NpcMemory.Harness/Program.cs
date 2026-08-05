using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json.Linq;

namespace NpcMemory.Harness
{
    /// <summary>
    /// The console harness — every demo beat headless against a live
    /// `python -m app.serve` (fake or real mode). This IS the Wk-1
    /// Unity<->backend interop go/no-go (unity-client.md done-when 4): it
    /// provisions its own agent over the API, proves the tri-state
    /// serialization contract against the live gate, and walks provision ->
    /// observe -> loader -> correction-override -> chain inspection ->
    /// drift + cache -> gate fire -> warm-init -> SSE stream -> the
    /// weights-on-speech re-rank (A1 re-shape, 2026-08-04).
    /// Structural asserts only: IDs, flags, byte-identity — never prose.
    /// </summary>
    internal static class Program
    {
        private static int _checks;

        private static void Check(bool condition, string criterion, string detail = "")
        {
            if (!condition)
            {
                Console.WriteLine($"  FAIL  {criterion}" + (detail == "" ? "" : $"  ({detail})"));
                Environment.Exit(1);
            }
            _checks++;
            Console.WriteLine($"  PASS  {criterion}" + (detail == "" ? "" : $"  ({detail})"));
        }

        private static async Task<int> Main(string[] args)
        {
            var baseUrl = "http://127.0.0.1:8000";
            for (var i = 0; i < args.Length - 1; i++)
            {
                if (args[i] == "--base-url")
                {
                    baseUrl = args[i + 1];
                }
            }
            Console.WriteLine($"NpcMemory harness -> {baseUrl}");
            using var client = new NpcMemoryClient(baseUrl);

            // -- [1] provision the agent over the API ----------------------
            Console.WriteLine("\n[1] Provision the demo agent (POST /v1/agents)");
            var created = await client.CreateAgentAsync(new CreateAgentRequest
            {
                Name = "harness-keeper",
                SeedIdentity = "I keep the ford and remember who pays their toll.",
                DiagnosticityGoal = "what threatens the ford",
                Config = new JObject
                {
                    // Taus chosen for the beat arithmetic: at t0 the 2-day-old
                    // observes sit well inside theta (verbatim); at t0+46d they
                    // are far past it (reconstructed).
                    ["decay_classes"] = new JObject
                    {
                        ["episodic"] = 604800.0,
                        ["semantic"] = 2592000.0,
                    },
                    ["decay_class_default"] = "episodic",
                },
            });
            Check(created.AgentId != Guid.Empty, "agent provisioned, server-minted UUID",
                created.AgentId.ToString());

            var session = new NpcSession(client, created.AgentId, phaseTag: "harness");

            // -- [2] observes at injected world times ----------------------
            Console.WriteLine("\n[2] Observes at injected timestamps (time travel)");
            var t0 = new DateTimeOffset(2026, 7, 27, 12, 0, 0, TimeSpan.Zero);
            session.AsOf = t0.AddDays(-2);
            var obsToll = await session.ObserveAsync(
                "The miller raised his toll at the bridge and the carters grumbled all week.");
            session.AsOf = t0.AddDays(-1);
            var obsStorm = await session.ObserveAsync(
                "A late storm flattened the barley on the south slope before dusk.");
            session.AsOf = t0.AddHours(-6);
            var obsCoin = await session.ObserveAsync(
                "A stranger paid the ford toll in foreign coin and would not give a name.");
            Check(
                obsToll.MemoryId != Guid.Empty && obsStorm.MemoryId != Guid.Empty
                    && obsCoin.MemoryId != Guid.Empty,
                "three observes landed with IDs + computed facts",
                $"decay_class={obsCoin.DecayClass}");

            // -- [3] scene start freezes state -----------------------------
            session.AsOf = t0;
            var scene1 = await session.SceneBoundaryAsync("ford");
            Check(
                scene1.Accepted && session.IdentityVersion != null
                    && session.SceneStartedAt == t0,
                "scene boundary froze identity_version + basis",
                $"identity={session.IdentityVersion?.Substring(0, 8)}…");

            // -- [4] loader turn + the tri-state contract ------------------
            Console.WriteLine("\n[4] Loader turn, then the null-vs-[] tri-state proof");
            var loader = await session.SayAsync("What has happened at the ford lately?");
            Check(
                !loader.Instrumentation.Retrieval.Gate.Evaluated,
                "null loaded set -> LOADER turn (gate not evaluated)");
            Check(
                loader.Items.Count > 0
                    && loader.Items.All(i => i.MemoryId != Guid.Empty)
                    && loader.Items.All(i => i.ReadMode == "verbatim"),
                "IDs + scores + read_mode on every served item",
                $"{loader.Items.Count} items, top score {loader.Items[0].Score:F3}");
            Check(
                session.LoadedMemoryIds != null
                    && session.LoadedMemoryIds.SequenceEqual(
                        loader.Items.Select(i => i.MemoryId)),
                "NpcSession bookkeeping: served IDs became the loaded set");

            var gated = await session.SayAsync("And the miller?");
            Check(
                gated.Instrumentation.Retrieval.Gate.Evaluated,
                "populated loaded set -> gate evaluated mid-scene");

            // The wire proof that [] != null: an EMPTY list still evaluates.
            var emptyListTurn = await client.DialogueTurnAsync(new DialogueTurnRequest
            {
                AgentId = created.AgentId,
                Utterance = "Anything at all?",
                AsOf = t0,
                IdentityVersion = session.IdentityVersion,
                SceneStartedAt = session.SceneStartedAt,
                LoadedMemoryIds = new List<Guid>(),
            });
            Check(
                emptyListTurn.Instrumentation.Retrieval.Gate.Evaluated,
                "[] serialized as an empty list -> gate EVALUATED (tri-state honest)");

            // -- [5] SSE streaming turn ------------------------------------
            Console.WriteLine("\n[5] SSE streaming turn (/v1/dialogue/turn/stream)");
            var chunks = new StringBuilder();
            var chunkCount = 0;
            var streamed = await session.SayStreamAsync(
                "Tell me about the stranger.",
                chunk => { chunks.Append(chunk); chunkCount++; });
            Check(
                chunkCount > 0 && chunks.ToString() == streamed.Content,
                "chunks streamed live and concatenate byte-identically to content",
                $"{chunkCount} chunks");
            var ins = streamed.Instrumentation;
            Check(
                ins.PerceivedFirstWordMs > ins.FirstWordMs && ins.FirstWordMs > 0.0,
                "perceived_first_word_ms > first_word_ms > 0 (the <1 s bar's field)",
                $"perceived {ins.PerceivedFirstWordMs:F1} ms vs first_word {ins.FirstWordMs:F1} ms");

            // -- [6] correction-override + the chain (The Ledger's read) ---
            Console.WriteLine("\n[6] Correction-override + chain inspection");
            var correctedText =
                "The stranger paid the ford toll in iron tokens and gave the name Aldous.";
            var correction = await session.CorrectAsync(obsCoin.MemoryId, correctedText);
            Check(
                correction.DetailId != correction.SupersededDetailId
                    && correction.FactVersionId != correction.SupersededFactVersionId,
                "correction swapped BOTH heads (telling + fact)",
                $"evicted {correction.EvictedCacheRows} cache rows");
            var chain = await client.MemoryChainAsync(obsCoin.MemoryId);
            Check(
                chain.Details.Select(d => d.WriteCause)
                    .SequenceEqual(new[] { "original", "authorial_correction" })
                    && chain.Details.Select(d => d.IsLive)
                        .SequenceEqual(new[] { false, true })
                    && chain.Details[1].Content == correctedText
                    && chain.Details[0].InvalidAt == chain.Details[1].ValidAt,
                "chain route: superseded row PRESENT, corrected head live, coherent timeline");
            Check(
                chain.Facts.All(f => f.HasEmbedding)
                    && chain.Facts[1].BasisText == correctedText,
                "fact chain rides beside the telling chain");
            var followUp = await session.SayAsync(correctedText);
            var servedCorrected = followUp.Items.FirstOrDefault(
                i => i.MemoryId == obsCoin.MemoryId);
            Check(
                servedCorrected != null && servedCorrected.Content == correctedText,
                "the next serve of that memory is the corrected telling, byte-verbatim");

            var index = await client.AgentMemoriesAsync(created.AgentId);
            Check(
                index.TotalCount == 3
                    && index.Memories.Single(m => m.MemoryId == obsCoin.MemoryId)
                        .LiveContent == correctedText
                    && index.Memories.Single(m => m.MemoryId == obsCoin.MemoryId)
                        .DetailCount == 2,
                "index route: the live telling head beside each memory");

            // -- [7] reconstructive drift across a 46-day jump -------------
            Console.WriteLine("\n[7] 46-day jump: reconstruction + within-scene byte-identity");
            session.AsOf = t0.AddDays(46);
            await session.SceneBoundaryAsync("ford-later");
            var drifted = await session.SayAsync("What do you remember of the old days?");
            var recon = drifted.Instrumentation.Retrieval;
            Check(
                drifted.Items.Any(i => i.ReadMode == "reconstructed")
                    && (recon.WriteBacks > 0 || recon.CacheHits > 0),
                "past-theta items served RECONSTRUCTED with write-back/cache",
                $"write_backs={recon.WriteBacks} cache_hits={recon.CacheHits} refusals={recon.DriftRefusals}");
            var reread = await session.SayAsync("What do you remember of the old days?");
            var byId = reread.Items.ToDictionary(i => i.MemoryId, i => i.Content);
            Check(
                reread.Instrumentation.Retrieval.CacheHits > 0
                    && drifted.Items.Where(i => byId.ContainsKey(i.MemoryId))
                        .All(i => byId[i.MemoryId] == i.Content),
                "within-scene reread: cache-hit and byte-identical served text");

            // The judge-free metrics read (eval-harness.md stage 1): every
            // served-reconstructed item has a cache row (write-back, hit, or
            // refusal all leave one), so bands are non-empty; structural
            // consistency only — the ratio VALUES are the eval story's, not
            // this gate's.
            var reconItem = drifted.Items.First(i => i.ReadMode == "reconstructed");
            var metrics = await client.ReconstructionMetricsAsync(reconItem.MemoryId);
            Check(
                metrics.MemoryId == reconItem.MemoryId
                    && metrics.AgentId == created.AgentId
                    && metrics.LiveDetailId != null
                    && metrics.CacheBands.Count > 0
                    && (metrics.GistPrecision == null) == (metrics.GistFactsTotal == 0)
                    && metrics.GistFactsPresent <= metrics.GistFactsTotal,
                "metrics route: judge-free numbers on the reconstructed chain",
                $"gist {metrics.GistFactsPresent}/{metrics.GistFactsTotal}, "
                + $"bands=[{string.Join(",", metrics.CacheBands)}]");

            // -- [8] mid-scene gate fire -----------------------------------
            Console.WriteLine("\n[8] Mid-scene gate fire on a novel utterance");
            var obsHerons = await session.ObserveAsync(
                "Nine grey herons circled the weir at dawn, quarrelling over eels.");
            var before = session.LoadedMemoryIds!.Count;
            var novel = await session.SayAsync(
                "Nine grey herons circled the weir, did you see them quarrelling?");
            var gate = novel.Instrumentation.Retrieval.Gate;
            Check(
                gate.Evaluated && gate.Fired && gate.FetchedNewCount > 0
                    && session.LoadedMemoryIds!.Count > before
                    && session.LoadedMemoryIds!.Contains(obsHerons.MemoryId),
                "gate fired, fetched the unseen memory, session appended it",
                $"signals=[{string.Join(",", gate.SignalsFired)}] fetched={gate.FetchedNewCount}");

            // -- [9] off-camera warm-init ----------------------------------
            Console.WriteLine("\n[9] Warm-init choreography (the camera-cut trick)");
            session.AsOf = t0.AddDays(92);
            await session.SceneBoundaryAsync("ford-much-later");
            var warm = await client.DialogueInitAsync(new DialogueInitRequest
            {
                AgentId = created.AgentId,
                QueryText = "the old days at the ford",
                AsOf = session.AsOf,
                IdentityVersion = session.IdentityVersion,
                SceneStartedAt = session.SceneStartedAt,
            });
            var onCamera = await session.SayAsync("Tell me again about the old days.");
            Check(
                onCamera.Instrumentation.Retrieval.CacheHits > 0
                    && onCamera.Instrumentation.Retrieval.WriteBacks == 0,
                "after the off-camera init, the on-camera read is a pure cache hit",
                $"init write_backs={warm.Instrumentation.WriteBacks}, turn cache_hits={onCamera.Instrumentation.Retrieval.CacheHits}");

            // -- [10] weights-on-speech (A1 re-shape, 2026-08-04) ----------
            Console.WriteLine("\n[10] Weights-on-speech: parity, then re-rank");
            // Raw stateless turns with a null loaded set (loader by
            // construction) so the parity contract applies: at default
            // weights DialogueView == the (id, score) projection of Items.
            // The utterance targets the 94-day-old toll observe, so at
            // t0+92d the base ranking is recency-dominated (the 46-day
            // herons observe tops it) while relevance favors the old toll
            // memory — zeroing the recency exponent must re-order.
            DialogueTurnRequest WeightsTurn(WeightOverrides? overrides) =>
                new DialogueTurnRequest
                {
                    AgentId = created.AgentId,
                    Utterance = "Who raised the toll at the bridge?",
                    AsOf = session.AsOf,
                    IdentityVersion = session.IdentityVersion,
                    SceneStartedAt = session.SceneStartedAt,
                    WeightOverrides = overrides,
                };
            var baseline = await client.DialogueTurnAsync(WeightsTurn(null));
            Check(
                baseline.DialogueView.Count > 0
                    && baseline.DialogueView.Select(v => v.MemoryId)
                        .SequenceEqual(baseline.Items.Select(i => i.MemoryId))
                    && baseline.DialogueView.Zip(baseline.Items, (v, i) => (v, i))
                        .All(p => Math.Abs(p.v.Score - p.i.Score) < 1e-12),
                "default weights: dialogue_view == the served ranking (parity)",
                $"{baseline.DialogueView.Count} refs");
            var overridden = await client.DialogueTurnAsync(
                WeightsTurn(new WeightOverrides { Recency = 0.0 }));
            Check(
                overridden.DialogueView.Count > 0
                    && new HashSet<Guid>(overridden.DialogueView.Select(v => v.MemoryId))
                        .SetEquals(overridden.Items.Select(i => i.MemoryId))
                    && !overridden.DialogueView.Select(v => v.MemoryId)
                        .SequenceEqual(overridden.Items.Select(i => i.MemoryId)),
                "override re-ranks the view feeding the prose prompt (same set, new order)",
                $"top {overridden.DialogueView[0].MemoryId.ToString().Substring(0, 8)}… "
                + $"vs served {overridden.Items[0].MemoryId.ToString().Substring(0, 8)}…");

            // -- [11] client-side instrumentation --------------------------
            // ClientTotalMs must be a REAL number after any call, whether or
            // not anything subscribed to OnCallMeasured. Its first shape only
            // wrote the property when a handler existed, so a caller that read
            // it without subscribing got a plausible-looking 0 (found by the
            // floor-verifier, 2026-07-28).
            Console.WriteLine("\n[11] Client-side timing (instrument at the seam)");
            using (var unsubscribed = new NpcMemoryClient(baseUrl))
            {
                await unsubscribed.AgentMemoriesAsync(created.AgentId, 1);
                Check(unsubscribed.ClientTotalMs > 0.0,
                    "ClientTotalMs is recorded with NO subscriber attached",
                    $"{unsubscribed.ClientTotalMs:F2} ms");
            }
            var measured = new List<string>();
            client.OnCallMeasured += (path, ms) => measured.Add(path);
            await client.AgentMemoriesAsync(created.AgentId, 1);
            Check(measured.Count == 1 && measured[0].StartsWith("/v1/agents/")
                    && client.ClientTotalMs > 0.0,
                "OnCallMeasured fires once per call with the route path",
                $"{measured[0]} @ {client.ClientTotalMs:F2} ms");

            // -- wrap-up ---------------------------------------------------
            Console.WriteLine(
                $"\nALL HARNESS BEATS PASSED ({_checks} checks)"
                + " — the interop gate is GREEN");
            return 0;
        }
    }
}
