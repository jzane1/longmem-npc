using System;
using System.Collections.Generic;
using System.IO;
using System.Net.Http;
using System.Text;
using System.Threading;
using System.Threading.Tasks;

namespace NpcMemory
{
    /// <summary>An HTTP error from the longmem-npc service, surfaced loudly —
    /// never swallowed, never silently retried (the service's fail-loud
    /// precedent). StatusCode 0 means a transport/contract failure.</summary>
    public sealed class NpcMemoryApiException : Exception
    {
        public int StatusCode { get; }

        public NpcMemoryApiException(int statusCode, string detail)
            : base($"longmem-npc API error {statusCode}: {detail}")
        {
            StatusCode = statusCode;
        }
    }

    /// <summary>
    /// The ONE flat client over the longmem-npc HTTP API (unity-client.md,
    /// ruled 2026-07-27: engine-agnostic, zero UnityEngine types, no
    /// abstraction ceremony). Stateless — scene state lives in NpcSession.
    /// Verbs mirror the routes 1:1 and are pass-through both ways: requests
    /// serialize exactly what the service accepts; responses deserialize
    /// every field the service returns.
    ///
    /// Timeouts are per-route and integrator-configurable (nothing
    /// hardcoded beyond overridable defaults): Init must tolerate the cold
    /// reconstruction pre-warm (16.3 s measured real-mode), Turn the full
    /// turn, Observe the synchronous write pass.
    ///
    /// Deliberately NO ConfigureAwait(false) anywhere: continuations honor
    /// the caller's SynchronizationContext, so in Unity every await — and
    /// every callback (chunks, directives, reputation) — resumes on the
    /// main thread with no explicit marshaling. The classic library-deadlock
    /// hazard needs a caller that BLOCKS on these tasks, and blocking
    /// (.Result/.Wait) is banned by the adapter contract. Play-mode-proven:
    /// the demo driver asserts chunk callbacks land on the main thread.
    /// </summary>
    public sealed class NpcMemoryClient : IDisposable
    {
        private readonly HttpClient _http;
        private readonly bool _ownsHttp;
        private readonly string _baseUrl;

        public TimeSpan InitTimeout { get; set; } = TimeSpan.FromSeconds(60);
        public TimeSpan TurnTimeout { get; set; } = TimeSpan.FromSeconds(60);
        public TimeSpan ObserveTimeout { get; set; } = TimeSpan.FromSeconds(30);
        public TimeSpan DefaultTimeout { get; set; } = TimeSpan.FromSeconds(15);

        public NpcMemoryClient(string baseUrl, HttpClient? http = null)
        {
            _baseUrl = baseUrl.TrimEnd('/');
            _ownsHttp = http == null;
            _http = http ?? new HttpClient();
            // Per-route timeouts ride CancellationTokens; the HttpClient-level
            // timeout must not undercut them.
            if (_ownsHttp)
            {
                _http.Timeout = Timeout.InfiniteTimeSpan;
            }
        }

        public void Dispose()
        {
            if (_ownsHttp)
            {
                _http.Dispose();
            }
        }

        // -- verbs (route table, unity-client.md) -----------------------

        public Task<CreateAgentResult> CreateAgentAsync(
            CreateAgentRequest request, CancellationToken ct = default) =>
            PostAsync<CreateAgentResult>("/v1/agents", request, DefaultTimeout, ct);

        public Task<IngestResult> ObserveAsync(
            ObserveEvent evt, CancellationToken ct = default) =>
            PostAsync<IngestResult>("/v1/events/observe", evt, ObserveTimeout, ct);

        public Task<SceneResult> SceneBoundaryAsync(
            SceneBoundaryEvent evt, CancellationToken ct = default) =>
            PostAsync<SceneResult>("/v1/events/scene-boundary", evt, DefaultTimeout, ct);

        public Task<PinResult> SetPinAsync(
            Guid memoryId, bool pinned, CancellationToken ct = default) =>
            SendAsync<PinResult>(
                HttpMethod.Put,
                $"/v1/memories/{memoryId}/pin",
                new PinRequest { Pinned = pinned },
                DefaultTimeout,
                ct);

        public Task<CorrectionResult> CorrectAsync(
            Guid memoryId, CorrectionRequest request, CancellationToken ct = default) =>
            PostAsync<CorrectionResult>(
                $"/v1/memories/{memoryId}/correction", request, DefaultTimeout, ct);

        public Task<RetrievalResult> DialogueInitAsync(
            DialogueInitRequest request, CancellationToken ct = default) =>
            PostAsync<RetrievalResult>("/v1/dialogue/init", request, InitTimeout, ct);

        public Task<DialogueTurnResult> DialogueTurnAsync(
            DialogueTurnRequest request, CancellationToken ct = default) =>
            PostAsync<DialogueTurnResult>("/v1/dialogue/turn", request, TurnTimeout, ct);

        public Task<MemoryChainResult> MemoryChainAsync(
            Guid memoryId, CancellationToken ct = default) =>
            GetAsync<MemoryChainResult>($"/v1/memories/{memoryId}/chain", ct);

        public Task<AgentMemoriesResult> AgentMemoriesAsync(
            Guid agentId, int? limit = null, CancellationToken ct = default) =>
            GetAsync<AgentMemoriesResult>(
                $"/v1/agents/{agentId}/memories" + (limit is int l ? $"?limit={l}" : ""),
                ct);

        /// <summary>
        /// The SSE turn (POST /v1/dialogue/turn/stream): onChunk fires per
        /// prose chunk as it arrives; onReconstructing fires if the server
        /// signals a blocking mid-scene retelling; returns the terminal
        /// DialogueTurnResult. Pre-stream service errors (404/422) throw
        /// NpcMemoryApiException exactly like the non-streaming route; an
        /// in-stream `error` event throws with StatusCode 0.
        /// </summary>
        public async Task<DialogueTurnResult> DialogueTurnStreamAsync(
            DialogueTurnRequest request,
            Action<string> onChunk,
            Action? onReconstructing = null,
            CancellationToken ct = default)
        {
            using var cts = CancellationTokenSource.CreateLinkedTokenSource(ct);
            cts.CancelAfter(TurnTimeout);
            using var message = new HttpRequestMessage(
                HttpMethod.Post, _baseUrl + "/v1/dialogue/turn/stream")
            {
                Content = new StringContent(
                    NpcJson.Serialize(request), Encoding.UTF8, "application/json"),
            };
            using var response = await _http
                .SendAsync(message, HttpCompletionOption.ResponseHeadersRead, cts.Token);
            if (!response.IsSuccessStatusCode)
            {
                var detail = await response.Content.ReadAsStringAsync();
                throw new NpcMemoryApiException((int)response.StatusCode, detail);
            }

            using var stream = await response.Content.ReadAsStreamAsync();
            using var reader = new StreamReader(stream, Encoding.UTF8);

            DialogueTurnResult? result = null;
            string? eventName = null;
            string? data = null;
            while (!reader.EndOfStream)
            {
                var line = await reader.ReadLineAsync();
                if (line == null)
                {
                    break;
                }
                if (line.StartsWith("event: ", StringComparison.Ordinal))
                {
                    eventName = line.Substring(7);
                }
                else if (line.StartsWith("data: ", StringComparison.Ordinal))
                {
                    data = line.Substring(6);
                }
                else if (line.Length == 0 && eventName != null)
                {
                    switch (eventName)
                    {
                        case "chunk":
                            onChunk(NpcJson.Deserialize<string>(data ?? "\"\""));
                            break;
                        case "reconstructing":
                            onReconstructing?.Invoke();
                            break;
                        case "result":
                            result = NpcJson.Deserialize<DialogueTurnResult>(data ?? "");
                            break;
                        case "error":
                            throw new NpcMemoryApiException(
                                0, NpcJson.Deserialize<string>(data ?? "\"stream error\""));
                    }
                    eventName = null;
                    data = null;
                }
            }
            return result
                ?? throw new NpcMemoryApiException(0, "stream ended without a result event");
        }

        // -- transport ---------------------------------------------------

        private Task<T> PostAsync<T>(
            string path, object body, TimeSpan timeout, CancellationToken ct) =>
            SendAsync<T>(HttpMethod.Post, path, body, timeout, ct);

        private async Task<T> GetAsync<T>(string path, CancellationToken ct)
        {
            using var cts = CancellationTokenSource.CreateLinkedTokenSource(ct);
            cts.CancelAfter(DefaultTimeout);
            using var response = await _http
                .GetAsync(_baseUrl + path, cts.Token);
            return await ReadAsync<T>(response);
        }

        private async Task<T> SendAsync<T>(
            HttpMethod method, string path, object body, TimeSpan timeout,
            CancellationToken ct)
        {
            using var cts = CancellationTokenSource.CreateLinkedTokenSource(ct);
            cts.CancelAfter(timeout);
            using var message = new HttpRequestMessage(method, _baseUrl + path)
            {
                Content = new StringContent(
                    NpcJson.Serialize(body), Encoding.UTF8, "application/json"),
            };
            using var response = await _http.SendAsync(message, cts.Token);
            return await ReadAsync<T>(response);
        }

        private static async Task<T> ReadAsync<T>(HttpResponseMessage response)
        {
            var text = await response.Content.ReadAsStringAsync();
            if (!response.IsSuccessStatusCode)
            {
                throw new NpcMemoryApiException((int)response.StatusCode, text);
            }
            return NpcJson.Deserialize<T>(text);
        }
    }
}
