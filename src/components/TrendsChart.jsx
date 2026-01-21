import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';

/**
 * Renders the custom Neo-brutalist tooltip.
 */
const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-white border-2 border-black shadow-neo p-3 font-sans text-sm font-bold">
                <p className="mb-2 underline decoration-2">{label}</p>
                {payload.map((entry, index) => (
                    <p key={index} style={{ color: entry.fill }}>
                        {entry.name}: {entry.value}
                    </p>
                ))}
            </div>
        );
    }
    return null;
};

const TrendsChart = ({ data }) => {
    return (
        <div className="w-full h-[400px] bg-white border-3 border-black shadow-neo p-4 md:p-6 mb-8 rounded-none">
            <h3 className="text-2xl font-black mb-6 uppercase tracking-tight">Weekly Mood Trends</h3>

            <ResponsiveContainer width="100%" height="100%">
                <BarChart
                    data={data}
                    margin={{
                        top: 5,
                        right: 10,
                        left: -20,
                        bottom: 5,
                    }}
                >
                    <XAxis
                        dataKey="name"
                        axisLine={{ stroke: '#000', strokeWidth: 3 }}
                        tickLine={{ stroke: '#000', strokeWidth: 2 }}
                        tick={{ fill: '#000', fontSize: 12, fontWeight: 'bold' }}
                        dy={10}
                    />
                    <YAxis
                        axisLine={{ stroke: '#000', strokeWidth: 3 }}
                        tickLine={{ stroke: '#000', strokeWidth: 2 }}
                        tick={{ fill: '#000', fontSize: 12, fontWeight: 'bold' }}
                    />
                    <Tooltip content={<CustomTooltip />} cursor={{ fill: '#000', opacity: 0.1 }} />

                    <Bar dataKey="energy" name="Energy" fill="var(--primary)" stroke="#000" strokeWidth={2} radius={[4, 4, 0, 0]} />
                    <Bar dataKey="happiness" name="Happiness" fill="var(--secondary)" stroke="#000" strokeWidth={2} radius={[4, 4, 0, 0]} />
                    <Bar dataKey="sadness" name="Sadness" fill="var(--accent)" stroke="#000" strokeWidth={2} radius={[4, 4, 0, 0]} />
                </BarChart>
            </ResponsiveContainer>
        </div>
    );
};

export default TrendsChart;
