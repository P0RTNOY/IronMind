import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

interface DataPoint {
    date: string;
    signups: number;
    active: number;
}

interface AnalyticsChartProps {
    data: DataPoint[];
    loading?: boolean;
}

export const AnalyticsChart: React.FC<AnalyticsChartProps> = ({ data, loading }) => {
    if (loading) {
        return (
            <div className="h-64 flex items-center justify-center border border-white/5 rounded-2xl bg-[#111] animate-pulse">
                <span className="text-gray-500 font-bold uppercase tracking-widest text-xs">Loading Analytics...</span>
            </div>
        );
    }

    if (!data || data.length === 0) {
        return (
            <div className="h-64 flex items-center justify-center border border-white/5 rounded-2xl bg-[#111]">
                <span className="text-gray-500 font-bold uppercase tracking-widest text-xs">No Data Available</span>
            </div>
        );
    }

    return (
        <div className="h-80 w-full bg-[#111] border border-white/5 rounded-2xl p-4">
            <h3 className="text-xs font-black uppercase tracking-widest text-gray-400 mb-6 ml-2">User Growth (30 Days)</h3>
            <ResponsiveContainer width="100%" height="85%">
                <LineChart data={data}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                    <XAxis
                        dataKey="date"
                        stroke="#666"
                        tick={{ fontSize: 10 }}
                        tickFormatter={(val) => val.slice(5)} // Show MM-DD
                        interval="preserveStartEnd"
                    />
                    <YAxis stroke="#666" tick={{ fontSize: 10 }} />
                    <Tooltip
                        contentStyle={{ backgroundColor: '#000', borderColor: '#333', borderRadius: '8px' }}
                        itemStyle={{ fontSize: '12px', fontWeight: 'bold' }}
                    />
                    <Legend wrapperStyle={{ fontSize: '10px', paddingTop: '10px' }} />
                    <Line
                        type="monotone"
                        dataKey="signups"
                        name="New Signups"
                        stroke="#ef4444"
                        strokeWidth={3}
                        dot={false}
                        activeDot={{ r: 6 }}
                    />
                    <Line
                        type="monotone"
                        dataKey="active"
                        name="Active Users"
                        stroke="#3b82f6"
                        strokeWidth={3}
                        dot={false}
                        activeDot={{ r: 6 }}
                    />
                </LineChart>
            </ResponsiveContainer>
        </div>
    );
};
