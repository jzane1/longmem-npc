using System;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using UnityEngine;

namespace NpcMemory.Unity
{
    /// <summary>
    /// The gray-box demo surface (unity-client.md fork 7, settled at build:
    /// an IMGUI dev-tool overlay — the intended systems aesthetic — over the
    /// primitive set; dialogue streams into the panel, the directive flashes
    /// the NPC body, reputation/gate lines read out live).
    ///
    /// autoRun plays a scripted Play-mode verification: provision → observes
    /// at injected times → boundary → loader turn → streamed turn — logging
    /// [npc-demo] receipts the MCP console read can assert on. It proves the
    /// ADAPTER contract (the full beat coverage is the console harness's
    /// floor): async work never blocks the main thread (frames keep pumping,
    /// asserted), and every callback lands ON the main thread (thread-id
    /// asserted).
    /// </summary>
    public sealed class NpcDemoDriver : MonoBehaviour
    {
        public NpcMemoryNpc npc;

        [Tooltip("Renderer flashed when a directive resolves (the capsule).")]
        public Renderer directiveFlashTarget;

        [Tooltip("Run the scripted Play-mode verification beats on Start.")]
        public bool autoRun;

        private string _input = "What has happened at the ford lately?";
        private string _dialogue = "";
        private string _status = "(connecting…)";
        private string _lastDirective = "-";
        private string _gateLine = "-";
        private double _reputation;
        private bool _busy;
        private int _frames;
        private int _mainThreadId;

        private void Awake()
        {
            // Keep the player loop pumping when the window is unfocused —
            // the demo records and verifies unattended (without this, an
            // unfocused Editor pauses Update while the sync context still
            // pumps, and the frame-pump proof reads zero).
            Application.runInBackground = true;
            _mainThreadId = Thread.CurrentThread.ManagedThreadId;
            if (npc != null)
            {
                npc.OnDirective += HandleDirective;
                npc.OnReputationChanged += (prev, after) => _reputation = after;
            }
        }

        private void Update()
        {
            _frames++;
        }

        private Color _flashOriginal;
        private bool _flashOriginalCaptured;

        private async void HandleDirective(ActionDirective directive)
        {
            _lastDirective = directive.Type;
            if (directiveFlashTarget != null)
            {
                // Capture the true original ONCE — overlapping flashes must
                // never capture each other's yellow as "original".
                if (!_flashOriginalCaptured)
                {
                    _flashOriginal = directiveFlashTarget.material.color;
                    _flashOriginalCaptured = true;
                }
                directiveFlashTarget.material.color = Color.yellow;
                await Task.Delay(400);
                if (directiveFlashTarget != null)
                {
                    directiveFlashTarget.material.color = _flashOriginal;
                }
            }
        }

        private async void Start()
        {
            if (!autoRun)
            {
                return;
            }
            try
            {
                await RunBeatsAsync();
            }
            catch (Exception exc)
            {
                Debug.LogException(exc, this);
                Debug.LogError("[npc-demo] PLAY-MODE BEATS FAILED");
            }
        }

        private int _checks;

        private void Check(bool condition, string criterion, string detail = "")
        {
            if (!condition)
            {
                throw new InvalidOperationException(
                    $"[npc-demo] FAIL {criterion} {detail}");
            }
            _checks++;
            Debug.Log($"[npc-demo] PASS {criterion}"
                + (detail == "" ? "" : $" ({detail})"));
        }

        private async Task RunBeatsAsync()
        {
            // Wait for the adapter's own Start() to finish provisioning.
            var deadline = Time.realtimeSinceStartup + 30f;
            while (npc == null || !npc.Ready)
            {
                if (Time.realtimeSinceStartup > deadline)
                {
                    throw new TimeoutException("[npc-demo] adapter never became Ready");
                }
                await Task.Yield();
            }
            _status = $"agent {npc.AgentId}";
            Check(true, "adapter provisioned over the API", npc.AgentId.ToString());

            var t0 = new DateTimeOffset(2026, 7, 27, 12, 0, 0, TimeSpan.Zero);
            npc.SetAsOf(t0.AddDays(-2));
            await npc.ObserveAsync(
                "The miller raised his toll at the bridge and the carters grumbled all week.");
            npc.SetAsOf(t0.AddHours(-6));
            var coin = await npc.ObserveAsync(
                "A stranger paid the ford toll in foreign coin and would not give a name.");
            Check(coin.MemoryId != Guid.Empty, "observes landed at injected world times");

            npc.SetAsOf(t0);
            var scene = await npc.SceneBoundaryAsync("graybox");
            Check(
                scene.Accepted && npc.Session.IdentityVersion != null,
                "scene boundary froze identity + basis");

            var framesBefore = _frames;
            var loader = await npc.SayAsync(_input);
            _dialogue = loader.Content;
            _gateLine = GateLine(loader);
            Check(
                !loader.Instrumentation.Retrieval.Gate.Evaluated
                    && loader.Items.Count > 0,
                "loader turn served IDs + scores",
                $"{loader.Items.Count} items");

            var chunkThread = -1;
            var chunks = new StringBuilder();
            _dialogue = "";
            var streamed = await npc.SayStreamAsync(
                "Tell me about the stranger.",
                chunk =>
                {
                    chunkThread = Thread.CurrentThread.ManagedThreadId;
                    chunks.Append(chunk);
                    _dialogue += chunk; // live on-screen streaming
                });
            _gateLine = GateLine(streamed);
            Check(
                chunks.ToString() == streamed.Content,
                "streamed chunks == content, rendered live");
            Check(
                chunkThread == _mainThreadId,
                "chunk callbacks land ON the main thread",
                $"thread {chunkThread}");
            Check(
                streamed.Instrumentation.Retrieval.Gate.Evaluated,
                "second turn gated (session bookkeeping live in-engine)");
            Check(
                _frames > framesBefore,
                "the main thread kept pumping frames through both turns",
                $"+{_frames - framesBefore} frames");

            Debug.Log(
                $"[npc-demo] ALL PLAY-MODE BEATS PASSED ({_checks} checks) — "
                + "the Unity adapter contract holds");
        }

        private static string GateLine(DialogueTurnResult result)
        {
            var gate = result.Instrumentation.Retrieval.Gate;
            return gate.Evaluated
                ? $"gate: evaluated fired={gate.Fired} new={gate.FetchedNewCount}"
                : "gate: loader turn";
        }

        private void OnGUI()
        {
            // The dev-tool overlay IS the intended aesthetic (ruled 2026-07-22).
            GUILayout.BeginArea(new Rect(12, 12, 560, 320), GUI.skin.box);
            GUILayout.Label($"longmem-npc — {_status}");
            GUILayout.Label($"reputation: {_reputation:F3}   directive: {_lastDirective}");
            GUILayout.Label(_gateLine);
            GUILayout.Space(6);
            GUILayout.Label(_dialogue, GUILayout.Height(140));
            GUILayout.Space(6);
            _input = GUILayout.TextField(_input);
            GUI.enabled = !_busy && npc != null && npc.Ready;
            GUILayout.BeginHorizontal();
            if (GUILayout.Button("Say"))
            {
                RunUi(async () =>
                {
                    _dialogue = "";
                    var result = await npc.SayStreamAsync(
                        _input, chunk => _dialogue += chunk);
                    _gateLine = GateLine(result);
                });
            }
            if (GUILayout.Button("Observe"))
            {
                RunUi(async () => await npc.ObserveAsync(_input));
            }
            if (GUILayout.Button("Scene boundary"))
            {
                RunUi(async () => await npc.SceneBoundaryAsync("graybox"));
            }
            if (GUILayout.Button("+46 days"))
            {
                var now = npc.Session.AsOf ?? DateTimeOffset.UtcNow;
                npc.SetAsOf(now.AddDays(46));
            }
            GUILayout.EndHorizontal();
            GUI.enabled = true;
            GUILayout.EndArea();
        }

        private async void RunUi(Func<Task> action)
        {
            _busy = true;
            try
            {
                await action();
            }
            catch (Exception exc)
            {
                Debug.LogException(exc, this);
            }
            finally
            {
                _busy = false;
            }
        }
    }
}
