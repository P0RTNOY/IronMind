import React, { useEffect, useState } from 'react';
import { apiFetch } from '../../lib/api';
import { toast } from '../../components/toast';
import { Loading } from '../../components/Layout';

interface PaymentEvent {
    id: string;
    provider: string;
    type: string;
    receivedAt: string;
    payload_raw_redacted?: any;
    payload_keys?: string[];
    transaction_keys?: string[];
    providerRefCandidate?: string;
    transactionUidCandidate?: string;
    providerSubscriptionIdCandidate?: string;
    verifyMode?: string;
    unmapped?: boolean;
    unmappedHint?: {
        raw_status_code?: string;
        raw_status?: string;
        raw_transaction_type?: string;
    };
}

const DEV_FIXTURES: Record<string, string> = {
    "approved": '{\n  "payment_request_uid": "pp_req_ok_001",\n  "transaction": {\n    "uid": "txn_ok_001",\n    "status_code": "000",\n    "status": "approved"\n  }\n}',
    "declined": '{\n  "payment_request_uid": "pp_req_fail_001",\n  "transaction": {\n    "uid": "txn_fail_001",\n    "status_code": "999",\n    "status": "declined"\n  }\n}',
    "unmapped": '{\n  "payment_request_uid": "pp_req_unmapped_001",\n  "transaction": {\n    "uid": "txn_unmapped_001",\n    "status_code": "777",\n    "status": "pending_review",\n    "type": "weird_new_type"\n  }\n}',
    "sub_renewed": '{\n  "payment_request_uid": "pp_req_sub_renew_001",\n  "transaction": {\n    "uid": "txn_sub_renew_001",\n    "status_code": "000",\n    "status": "approved",\n    "type": "recurring_renewal"\n  },\n  "recurring_id": "rec_sub_001"\n}',
    "sub_canceled": '{\n  "payment_request_uid": "pp_req_sub_cancel_001",\n  "transaction": {\n    "uid": "txn_sub_cancel_001",\n    "type": "recurring_canceled"\n  },\n  "recurring_id": "rec_sub_001"\n}',
    "sub_past_due": '{\n  "payment_request_uid": "pp_req_sub_past_due_001",\n  "transaction": {\n    "uid": "txn_sub_past_due_001",\n    "status_code": "999",\n    "status": "declined",\n    "type": "recurring_renewal"\n  },\n  "recurring_id": "rec_sub_001"\n}',
};

const AdminPayments: React.FC = () => {
    const [events, setEvents] = useState<PaymentEvent[]>([]);
    const [loading, setLoading] = useState(true);
    const [copyFailed, setCopyFailed] = useState(false);

    // Webhook Replay State
    const [replayPayload, setReplayPayload] = useState('{\n  "payment_request_uid": "pp_req_demo_1",\n  "transaction": {"uid": "txn_demo_1", "status_code": "000", "status": "approved"},\n  "recurring_id": "rec_demo_1"\n}');
    const [replayProvider, setReplayProvider] = useState('payplus');
    const [replayHeaders, setReplayHeaders] = useState('{"hash":"replay"}');
    const [replayForceLogOnly, setReplayForceLogOnly] = useState(true);
    const [replayLoading, setReplayLoading] = useState(false);
    const [replayResult, setReplayResult] = useState<any>(null);

    useEffect(() => {
        const fetchEvents = async () => {
            try {
                const data = await apiFetch('/admin/payments/events?limit=50');
                if (Array.isArray(data)) {
                    // Sort descending by receivedAt just in case
                    const sorted = [...data].sort((a, b) =>
                        new Date(b.receivedAt || 0).getTime() - new Date(a.receivedAt || 0).getTime()
                    );
                    setEvents(sorted);
                }
            } catch (err) {
                toast.error("Failed to load payment events.");
            } finally {
                setLoading(false);
            }
        };
        fetchEvents();
    }, []);

    const payplusEvents = events.filter(e => e.provider === 'payplus');
    const latestEvent = payplusEvents.length > 0 ? payplusEvents[0] : null;

    const handleCopyJson = async () => {
        if (!latestEvent || !latestEvent.payload_raw_redacted) return;

        const jsonStr = JSON.stringify(latestEvent.payload_raw_redacted, null, 2);

        try {
            if (navigator.clipboard && window.isSecureContext) {
                await navigator.clipboard.writeText(jsonStr);
                toast.success("JSON copied to clipboard!");
                setCopyFailed(false);
            } else {
                // Fallback triggered
                setCopyFailed(true);
            }
        } catch (err) {
            setCopyFailed(true);
        }
    };

    const handleLoadLatest = () => {
        if (latestEvent && latestEvent.payload_raw_redacted) {
            setReplayPayload(JSON.stringify(latestEvent.payload_raw_redacted, null, 2));
            toast.success("Loaded latest payload");
        } else {
            toast.info("No payload available");
        }
    };

    const handleReplay = async () => {
        try {
            setReplayLoading(true);
            setReplayResult(null);

            let parsedPayload;
            try {
                parsedPayload = JSON.parse(replayPayload);
            } catch (e) {
                toast.error("Invalid JSON in Payload field");
                return;
            }

            let parsedHeaders = {};
            try {
                if (replayHeaders.trim()) {
                    parsedHeaders = JSON.parse(replayHeaders);
                }
            } catch (e) {
                toast.error("Invalid JSON in Headers field");
                return;
            }

            const sizeBytes = new Blob([JSON.stringify(parsedPayload)]).size;
            if (sizeBytes > 50 * 1024) {
                toast.error(`Payload too large! (${sizeBytes} bytes, max 50KB)`);
                return;
            }

            const res = await apiFetch('/admin/payments/replay', {
                method: 'POST',
                body: JSON.stringify({
                    provider: replayProvider,
                    payload: parsedPayload,
                    headers: parsedHeaders,
                    force_log_only: replayForceLogOnly
                })
            });

            setReplayResult(res);
            toast.success("Webhook replayed successfully");

            // Re-fetch events briefly after test to refresh the list
            setTimeout(async () => {
                const refreshed = await apiFetch('/admin/payments/events?limit=50').catch(() => []);
                if (Array.isArray(refreshed) && refreshed.length > 0) {
                    setEvents([...refreshed].sort((a, b) => new Date(b.receivedAt || 0).getTime() - new Date(a.receivedAt || 0).getTime()));
                }
            }, 500);

        } catch (err: any) {
            toast.error(err.message || "Replay failed");
            setReplayResult({ error: err.message || "Unknown error" });
        } finally {
            setReplayLoading(false);
        }
    };

    if (loading) return <Loading />;

    const isUnmapped = latestEvent?.unmapped || latestEvent?.type === 'payplus.unmapped';

    return (
        <div className="space-y-6 max-w-5xl">
            <h1 className="text-3xl font-black uppercase tracking-wider">Payments Console</h1>

            {/* Webhook Replay Panel */}
            <section className="bg-[#111] border border-white/10 rounded overflow-hidden">
                <div className="bg-white/5 px-6 py-4 border-b border-white/10 flex justify-between items-center">
                    <h2 className="text-xl font-bold">Webhook Replay (Admin)</h2>
                    <div className="flex items-center gap-3">
                        {/* Only render the fixtures dropdown in development mode */}
                        {(import.meta as any).env?.DEV && (
                            <select
                                onChange={(e) => {
                                    if (e.target.value && DEV_FIXTURES[e.target.value]) {
                                        setReplayPayload(DEV_FIXTURES[e.target.value]);
                                        toast.success(`Loaded fixture: ${e.target.value}`);
                                        e.target.value = ''; // reset
                                    }
                                }}
                                className="text-xs font-bold bg-[#222] border border-white/20 hover:bg-[#333] text-white px-3 py-1.5 rounded transition min-w-[140px]"
                            >
                                <option value="">[DEV] Load Fixture...</option>
                                {Object.keys(DEV_FIXTURES).map(k => <option key={k} value={k}>{k}.json</option>)}
                            </select>
                        )}
                        <button
                            onClick={handleLoadLatest}
                            className="text-xs font-bold bg-white/10 hover:bg-white/20 text-white px-3 py-1.5 rounded transition disabled:opacity-50"
                            disabled={!latestEvent}
                        >
                            Load Latest Payload
                        </button>
                    </div>
                </div>

                <div className="p-6 grid grid-cols-1 lg:grid-cols-2 gap-8">
                    {/* Input Form */}
                    <div className="space-y-4">
                        <div className="flex gap-4">
                            <div className="flex-1">
                                <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Provider</label>
                                <select
                                    value={replayProvider}
                                    onChange={(e) => setReplayProvider(e.target.value)}
                                    className="w-full bg-black border border-white/10 rounded p-2 text-sm text-white"
                                >
                                    <option value="payplus">PayPlus</option>
                                    <option value="stub">Stub</option>
                                </select>
                            </div>
                            <div className="flex items-center pt-6">
                                <label className="flex items-center gap-2 cursor-pointer text-sm font-bold text-gray-300 hover:text-white transition">
                                    <input
                                        type="checkbox"
                                        checked={replayForceLogOnly}
                                        onChange={(e) => setReplayForceLogOnly(e.target.checked)}
                                        className="rounded bg-black border-white/20"
                                    />
                                    Force log_only mode
                                </label>
                            </div>
                        </div>

                        <div>
                            <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Headers (JSON)</label>
                            <textarea
                                value={replayHeaders}
                                onChange={(e) => setReplayHeaders(e.target.value)}
                                className="w-full bg-black border border-white/10 rounded p-3 text-xs font-mono text-gray-300 focus:outline-none focus:border-white/30 min-h-[60px]"
                            />
                        </div>

                        <div>
                            <div className="flex justify-between items-end mb-2">
                                <label className="block text-xs font-bold text-gray-400 uppercase tracking-widest">Payload (JSON)</label>
                                <span className="text-[10px] text-gray-500">{new Blob([replayPayload]).size} bytes</span>
                            </div>
                            <textarea
                                value={replayPayload}
                                onChange={(e) => setReplayPayload(e.target.value)}
                                className="w-full bg-black border border-white/10 rounded p-3 text-xs font-mono text-gray-300 focus:outline-none focus:border-white/30 min-h-[250px]"
                            />
                        </div>

                        <button
                            onClick={handleReplay}
                            disabled={replayLoading}
                            className="w-full bg-white text-black font-bold py-3 rounded hover:bg-gray-200 transition disabled:opacity-50"
                        >
                            {replayLoading ? 'Replaying...' : 'Replay Webhook'}
                        </button>
                    </div>

                    {/* Output Panel */}
                    <div className="flex flex-col h-full border border-white/10 rounded overflow-hidden">
                        <div className="bg-white/5 px-4 py-2 border-b border-white/10 flex justify-between items-center">
                            <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest">Replay Result</h3>
                            {replayResult && (
                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded uppercase ${replayResult.mutation_risk === 'safe' ? 'bg-green-500/20 text-green-400' : 'bg-yellow-500/20 text-yellow-500'
                                    }`}>
                                    {replayResult.mutation_risk === 'safe' ? '🛡️ Safe' : '⚠️ May Mutate State'}
                                </span>
                            )}
                        </div>
                        <div className="flex-1 bg-black p-4 overflow-auto flex flex-col gap-4">
                            {!replayResult ? (
                                <div className="h-full flex items-center justify-center text-gray-600 text-sm italic">
                                    No result yet
                                </div>
                            ) : (
                                <>
                                    {replayResult.provider_ref && (
                                        <div className="p-3 border border-white/10 rounded bg-[#111]">
                                            <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2 border-b border-white/10 pb-2">Intent Linking</h4>
                                            <div className="text-sm">
                                                {replayResult.intent_found ? (
                                                    <div className="text-green-400 font-bold flex items-center gap-2">
                                                        <span>✅</span>
                                                        <span>Intent Found: <span className="font-mono text-xs text-white">{replayResult.intent_id}</span></span>
                                                        <span className="text-gray-400 font-normal text-xs ml-1">(Status: {replayResult.intent_status})</span>
                                                    </div>
                                                ) : (
                                                    <div className="text-red-400 font-bold flex flex-col gap-1">
                                                        <div className="flex items-center gap-2">
                                                            <span>❌</span>
                                                            <span>No Matching Intent Found</span>
                                                        </div>
                                                        <span className="text-gray-400 font-normal text-xs ml-6">For provider_ref: {replayResult.provider_ref}</span>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                    <pre className="text-xs font-mono text-gray-300">
                                        {JSON.stringify(replayResult, null, 2)}
                                    </pre>
                                </>
                            )}
                        </div>
                    </div>
                </div>
            </section>

            <section className="bg-[#111] border border-white/10 rounded overflow-hidden">
                <div className="bg-white/5 px-6 py-4 border-b border-white/10 flex justify-between items-center">
                    <h2 className="text-xl font-bold">Schema Discovery (PayPlus)</h2>
                    {latestEvent && (
                        <div className="text-xs font-bold text-gray-400 bg-black px-3 py-1 rounded">
                            {new Date(latestEvent.receivedAt).toLocaleString()}
                        </div>
                    )}
                </div>

                <div className="p-6">
                    {!latestEvent ? (
                        <div className="text-center py-12 text-gray-400">
                            <p className="mb-2">No PayPlus events captured yet.</p>
                            <p className="italic text-sm">Hint: Send a webhook to `/webhooks/payments` to populate candidates.</p>
                        </div>
                    ) : (
                        <div className="space-y-8">
                            {isUnmapped && (
                                <div className="p-3 bg-yellow-500/10 border border-yellow-500/30 rounded text-yellow-400 text-sm font-bold">
                                    ⚠️ Unmapped PayPlus event captured
                                    {latestEvent.unmappedHint && (
                                        <span className="ml-2 font-mono text-xs font-normal text-yellow-500/70">
                                            status_code={latestEvent.unmappedHint.raw_status_code || '?'}{' '}
                                            status={latestEvent.unmappedHint.raw_status || '?'}{' '}
                                            type={latestEvent.unmappedHint.raw_transaction_type || '?'}
                                        </span>
                                    )}
                                </div>
                            )}

                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                                {/* Candidates Panel */}
                                <div className="space-y-6">
                                    <div>
                                        <h3 className="text-sm font-black text-gray-400 uppercase tracking-widest mb-3">Discovered Candidates</h3>
                                        <div className="space-y-3">
                                            <CandidateRow
                                                label="Provider Ref Candidate"
                                                value={latestEvent.providerRefCandidate}
                                                hint="Maps to PaymentIntent.providerRef"
                                            />
                                            <CandidateRow
                                                label="Transaction UID Candidate"
                                                value={latestEvent.transactionUidCandidate}
                                                hint="Used for idempotency / uniqueness"
                                            />
                                            <CandidateRow
                                                label="Subscription ID Candidate"
                                                value={latestEvent.providerSubscriptionIdCandidate}
                                                hint="Future recurring mapping / token replacement"
                                            />
                                            <CandidateRow
                                                label="Verify Mode"
                                                value={latestEvent.verifyMode}
                                                hint="log_only or enforce"
                                            />
                                        </div>
                                    </div>

                                    <div>
                                        <h3 className="text-sm font-black text-gray-400 uppercase tracking-widest mb-3">Payload Structure</h3>
                                        <div className="bg-black p-4 rounded text-xs font-mono text-gray-300 space-y-2 max-h-48 overflow-y-auto">
                                            <p><span className="text-blue-400">Top-Level Keys:</span> {latestEvent.payload_keys?.join(', ') || 'N/A'}</p>
                                            <p><span className="text-green-400">Transaction Keys:</span> {latestEvent.transaction_keys?.join(', ') || 'N/A'}</p>
                                        </div>
                                    </div>
                                </div>

                                {/* Raw Redacted JSON Panel */}
                                <div className="flex flex-col h-full">
                                    <div className="flex justify-between items-end mb-3">
                                        <h3 className="text-sm font-black text-gray-400 uppercase tracking-widest">Redacted Payload</h3>
                                        <button
                                            onClick={handleCopyJson}
                                            className="text-xs font-bold bg-white text-black px-3 py-1.5 rounded hover:bg-gray-200 transition"
                                        >
                                            Copy JSON
                                        </button>
                                    </div>

                                    {copyFailed ? (
                                        <div className="flex-1 min-h-[300px] flex flex-col">
                                            <div className="text-xs text-yellow-500 mb-2 font-bold">
                                                Clipboard failed (likely non-HTTPS). Select all and copy manually:
                                            </div>
                                            <textarea
                                                className="w-full flex-1 bg-black text-xs font-mono text-gray-300 p-4 border border-white/10 rounded focus:outline-none focus:border-white/30"
                                                readOnly
                                                value={JSON.stringify(latestEvent.payload_raw_redacted, null, 2)}
                                                onFocus={(e) => e.target.select()}
                                            />
                                        </div>
                                    ) : (
                                        <pre className="flex-1 bg-black text-xs font-mono text-gray-300 p-4 border border-white/10 rounded overflow-auto max-h-[400px]">
                                            {JSON.stringify(latestEvent.payload_raw_redacted, null, 2)}
                                        </pre>
                                    )}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </section>

            {/* Event List Table */}
            <section className="bg-[#111] border border-white/10 rounded overflow-hidden">
                <div className="bg-white/5 px-6 py-4 border-b border-white/10">
                    <h2 className="text-xl font-bold">Recent Webhook Events</h2>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-left text-sm">
                        <thead className="bg-black/50 text-gray-400 text-xs uppercase tracking-wider">
                            <tr>
                                <th className="p-4 font-bold">Received</th>
                                <th className="p-4 font-bold">Provider</th>
                                <th className="p-4 font-bold">Type</th>
                                <th className="p-4 font-bold">Candidate Ref</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {events.map((ev, i) => (
                                <tr key={i} className="hover:bg-white/5 transition">
                                    <td className="p-4 whitespace-nowrap text-gray-300">
                                        {new Date(ev.receivedAt).toLocaleString()}
                                    </td>
                                    <td className="p-4 font-mono text-xs">{ev.provider}</td>
                                    <td className="p-4 font-mono text-xs">
                                        {ev.type}
                                        {(ev.unmapped || ev.type === 'payplus.unmapped') && (
                                            <span className="ml-2 px-2 py-0.5 bg-yellow-500/20 text-yellow-400 text-[10px] font-bold rounded uppercase">
                                                Unmapped
                                            </span>
                                        )}
                                    </td>
                                    <td className="p-4 font-mono text-xs text-gray-400">
                                        {ev.providerRefCandidate || '-'}
                                        {ev.unmappedHint && (
                                            <span className="ml-2 text-[10px] text-yellow-500/70">
                                                status={ev.unmappedHint.raw_status || '?'} code={ev.unmappedHint.raw_status_code || '?'}
                                            </span>
                                        )}
                                    </td>
                                </tr>
                            ))}
                            {events.length === 0 && (
                                <tr>
                                    <td colSpan={4} className="p-8 text-center text-gray-500">
                                        No events found
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </section>
        </div>
    );
};

const CandidateRow: React.FC<{ label: string, value?: string, hint: string }> = ({ label, value, hint }) => (
    <div className="p-3 bg-black border border-white/5 rounded">
        <div className="flex justify-between items-start mb-1">
            <span className="text-xs font-bold text-gray-300">{label}</span>
            <span className="text-xs font-mono text-white bg-white/10 px-2 py-0.5 rounded ml-2 break-all text-right">
                {value || 'null'}
            </span>
        </div>
        <p className="text-[10px] text-gray-500">{hint}</p>
    </div>
);

export default AdminPayments;
