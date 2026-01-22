import { friendsData } from "@/lib/data"
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card"
import { cn } from "@/lib/utils"

export default function Compare() {
    return (
        <div className="space-y-8">
            <div>
                <h1 className="text-4xl font-black uppercase mb-2">Judge Your Friends</h1>
                <p className="text-xl font-medium text-muted-foreground">See who matches your vibe.</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {friendsData.map((friend) => {
                    const matchColor = friend.match > 80 ? 'bg-secondary' : (friend.match > 50 ? 'bg-primary' : 'bg-accent');

                    return (
                        <Card key={friend.name} className={cn("neo-brutal neo-brutal-hover transition-all cursor-crosshair", matchColor)}>
                            <CardHeader className="border-b-[3px] border-black pb-4">
                                <CardTitle className="flex justify-between items-center">
                                    <span>{friend.name}</span>
                                    <span className="text-xl bg-black text-white px-2 py-1 rotate-3 rounded-sm">
                                        {friend.match}%
                                    </span>
                                </CardTitle>
                            </CardHeader>
                            <CardContent className="pt-6">
                                <p className="font-bold text-lg">Top Genre:</p>
                                <p className="text-2xl font-black uppercase tracking-wider">{friend.topGenre}</p>
                            </CardContent>
                        </Card>
                    )
                })}
            </div>
        </div>
    )
}
