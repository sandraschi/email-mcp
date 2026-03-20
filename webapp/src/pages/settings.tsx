import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function Settings() {
    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-2xl font-bold tracking-tight text-white">Email Hub Settings</h2>
                <p className="text-slate-400">Manage email connectivity and AI reasoning configuration</p>
            </div>

            <div className="grid gap-6">
                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="text-white">Email Configuration</CardTitle>
                        <CardDescription className="text-slate-400">Connection details for IMAP/SMTP services</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid gap-2">
                            <Label className="text-slate-300">Email Address</Label>
                            <Input
                                className="bg-slate-900 border-slate-800 text-slate-100"
                                placeholder="sandra@vienna.at"
                            />
                        </div>
                        <div className="grid gap-2">
                            <Label className="text-slate-300">IMAP Server</Label>
                            <Input
                                className="bg-slate-900 border-slate-800 text-slate-100"
                                defaultValue="imap.vienna.at"
                            />
                        </div>
                        <Button variant="outline" className="border-slate-800 text-slate-300 hover:bg-slate-800">
                            Test Email Connectivity
                        </Button>
                    </CardContent>
                </Card>

                <Card className="border-slate-800 bg-slate-950/50">
                    <CardHeader>
                        <CardTitle className="text-white">Local LLM Interface</CardTitle>
                        <CardDescription className="text-slate-400">Settings for email reasoning and drafting</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="grid gap-2">
                            <Label className="text-slate-300">AI Provider</Label>
                            <Input
                                className="bg-slate-900 border-slate-800 text-slate-100"
                                defaultValue="ollama"
                            />
                        </div>
                        <div className="grid gap-2">
                            <Label className="text-slate-300">Model Name</Label>
                            <Input
                                className="bg-slate-900 border-slate-800 text-slate-100"
                                defaultValue="llama3.1-8b"
                            />
                        </div>
                        <Button variant="outline" className="border-slate-800 text-slate-300 hover:bg-slate-800">
                            Validate AI Endpoint
                        </Button>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
