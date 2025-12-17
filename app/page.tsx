"use client"

import { useState, useEffect } from "react"
import { Nav } from "@/components/nav"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Phone, CheckCircle2, AlertCircle, Loader2 } from "lucide-react"
import { VoiceCall } from "@/components/voice-call"

interface Call {
  id: string
  caller: string
  time: string
  status: "completed" | "in_progress" | "failed"
  escalated: boolean
}

export default function Dashboard() {
  const [serviceStatus, setServiceStatus] = useState<"running" | "stopped" | "error">("running")
  const [isStartingCall, setIsStartingCall] = useState(false)
  const [recentCalls, setRecentCalls] = useState<Call[]>([])
  const [isLoadingCalls, setIsLoadingCalls] = useState(true)

  useEffect(() => {
    // Fetch recent calls from GET /api/calls
    const fetchCalls = async () => {
      try {
        setIsLoadingCalls(true)
        const response = await fetch("/api/calls")
        if (!response.ok) throw new Error("Failed to fetch calls")
        const data = await response.json()
        setRecentCalls(data.calls.slice(0, 5)) // Show only 5 recent calls
      } catch (error) {
        console.error("[v0] Error fetching calls:", error)
        // Use placeholder data if API fails
        setRecentCalls([
          { id: "1", caller: "John Doe", time: "2 min ago", status: "completed", escalated: false },
          { id: "2", caller: "Jane Smith", time: "15 min ago", status: "completed", escalated: true },
          { id: "3", caller: "Bob Johnson", time: "1 hour ago", status: "completed", escalated: false },
          { id: "4", caller: "Alice Brown", time: "2 hours ago", status: "in_progress", escalated: false },
          { id: "5", caller: "Charlie Wilson", time: "3 hours ago", status: "failed", escalated: false },
        ])
      } finally {
        setIsLoadingCalls(false)
      }
    }

    fetchCalls()
  }, [])

  const handleStartDemoCall = async () => {
    setIsStartingCall(true)
    try {
      // Start voice call with Realtime session
      const response = await fetch("/api/call/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ org_id: "org_demo_001" }),
      })

      if (!response.ok) throw new Error("Failed to start call")

      const callData = await response.json()
      console.log("[v0] Call started:", callData)

      // Create Realtime session
      const sessionResponse = await fetch("/api/realtime/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ org_id: "org_demo_001" }),
      })

      if (!sessionResponse.ok) throw new Error("Failed to create session")

      const sessionData = await sessionResponse.json()
      console.log("[v0] Session created:", sessionData)

      // Show success and redirect to call page or show call interface
      alert(`Call started! Call ID: ${callData.call_id}\nSession ID: ${sessionData.session_id}\n\nNote: Full voice integration requires OpenAI Realtime WebSocket connection.`)
    } catch (error) {
      console.error("[v0] Error starting demo call:", error)
      alert("Failed to start demo call. Please try again.")
    } finally {
      setIsStartingCall(false)
    }
  }

  const getStatusColor = (status: Call["status"]) => {
    switch (status) {
      case "completed":
        return "text-success"
      case "in_progress":
        return "text-warning"
      case "failed":
        return "text-destructive"
    }
  }

  const getStatusLabel = (status: Call["status"]) => {
    return status.replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase())
  }

  return (
    <div className="min-h-screen bg-background">
      <Nav />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
            <p className="text-muted-foreground mt-1">Monitor your AI voice agent performance</p>
          </div>
        </div>

        <div className="grid gap-6 md:grid-cols-2 mb-8">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                Service Status
                {serviceStatus === "running" ? (
                  <Badge className="bg-success text-success-foreground">
                    <CheckCircle2 className="size-3 mr-1" />
                    Running
                  </Badge>
                ) : (
                  <Badge variant="destructive">
                    <AlertCircle className="size-3 mr-1" />
                    Stopped
                  </Badge>
                )}
              </CardTitle>
              <CardDescription>Voice agent service status</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                The voice agent is currently{" "}
                {serviceStatus === "running" ? "active and handling calls" : "not accepting calls"}.
              </p>
            </CardContent>
          </Card>

          <VoiceCall orgId="org_demo_001" />
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Recent Calls</CardTitle>
            <CardDescription>Latest voice agent interactions</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoadingCalls ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="size-6 animate-spin text-muted-foreground" />
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-border text-left">
                      <th className="pb-3 text-sm font-medium text-muted-foreground">Caller</th>
                      <th className="pb-3 text-sm font-medium text-muted-foreground">Time</th>
                      <th className="pb-3 text-sm font-medium text-muted-foreground">Status</th>
                      <th className="pb-3 text-sm font-medium text-muted-foreground">Escalated</th>
                    </tr>
                  </thead>
                  <tbody>
                    {recentCalls.map((call) => (
                      <tr key={call.id} className="border-b border-border last:border-0">
                        <td className="py-4 text-sm font-medium">{call.caller}</td>
                        <td className="py-4 text-sm text-muted-foreground">{call.time}</td>
                        <td className="py-4">
                          <span className={`text-sm font-medium ${getStatusColor(call.status)}`}>
                            {getStatusLabel(call.status)}
                          </span>
                        </td>
                        <td className="py-4">
                          {call.escalated ? (
                            <Badge variant="outline" className="text-warning border-warning">
                              Yes
                            </Badge>
                          ) : (
                            <span className="text-sm text-muted-foreground">No</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
