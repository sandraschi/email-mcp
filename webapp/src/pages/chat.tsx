import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Send, Bot, User } from "lucide-react";

export function Chat() {
    return (
        <div className="flex h-[calc(100vh-8rem)] flex-col space-y-4">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-2xl font-bold tracking-tight text-white">Command Interface</h2>
                    <p className="text-slate-400">Natural language robot control (LLM)</p>
                </div>
            </div>

            <Card className="flex-1 border-slate-800 bg-slate-950/50 flex flex-col overflow-hidden">
                <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
                    {/* Placeholder Chat History */}
                    <div className="flex gap-3">
                        <div className="h-8 w-8 rounded-full bg-slate-800 flex items-center justify-center border border-slate-700">
                            <User className="h-4 w-4 text-slate-400" />
                        </div>
                        <div className="flex-1 space-y-1">
                            <div className="flex items-center gap-2">
                                <span className="text-sm font-medium text-slate-200">Operator</span>
                                <span className="text-xs text-slate-500">10:42 AM</span>
                            </div>
                            <p className="text-sm text-slate-300 bg-slate-900/50 p-3 rounded-md border border-slate-800 inline-block">
                                "Find the last email from Steve regarding the database refactor and summarize it."
                            </p>
                        </div>
                    </div>

                    <div className="flex gap-3">
                        <div className="h-8 w-8 rounded-full bg-blue-900/20 flex items-center justify-center border border-blue-800">
                            <Bot className="h-4 w-4 text-blue-400" />
                        </div>
                        <div className="flex-1 space-y-1">
                            <div className="flex items-center gap-2">
                                <span className="text-sm font-medium text-blue-400">Mail AI</span>
                                <span className="text-xs text-slate-500">10:42 AM</span>
                            </div>
                            <div className="text-sm text-slate-300 bg-blue-950/10 p-3 rounded-md border border-blue-900/30 inline-block">
                                <p>Searching your inbox... I found an email from Steve Schipal sent 2 hours ago.</p>
                                <br />
                                <div className="p-3 bg-slate-950 rounded border border-slate-800 text-xs text-slate-400 italic">
                                    "Hey Sandra, the database refactor for the robotics-mcp is delayed. We need to standardize the bridge endpoints before we can proceed with the SOTA fleet expansion. Let's talk tomorrow."
                                </div>
                                <br />
                                <p className="text-blue-300 font-medium">Summary: Refactor delayed due to endpoint standardization requirements.</p>
                            </div>
                        </div>
                    </div>

                </CardContent>
                <div className="p-4 border-t border-slate-800 bg-slate-900/30">
                    <div className="flex gap-2">
                        <input
                            className="flex-1 bg-slate-950 border border-slate-800 rounded-md px-4 py-2 text-sm text-white focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"
                            placeholder="Ask me to search, draft, or organize your emails..."
                        />
                        <Button size="icon" className="bg-blue-600 hover:bg-blue-700">
                            <Send className="h-4 w-4" />
                        </Button>
                    </div>
                </div>
            </Card>
        </div>
    );
}
