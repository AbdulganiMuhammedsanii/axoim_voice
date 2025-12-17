"use client"

import { useState, useEffect } from "react"
import { Nav } from "@/components/nav"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Loader2, Phone, X } from "lucide-react"
import { Button } from "@/components/ui/button"

interface Call {
  id: string
  caller: string
  phone: string
  time: string
  duration: string
  status: "completed" | "in_progress" | "failed"
  escalated: boolean
  transcript: string
  intakeData: Record<string, any>
}

export default function CallLogsPage() {
  const [calls, setCalls] = useState<Call[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [selectedCall, setSelectedCall] = useState<Call | null>(null)

  useEffect(() => {
    // Fetch calls from GET /api/calls
    const fetchCalls = async () => {
      try {
        setIsLoading(true)
        const response = await fetch("/api/calls")
        if (!response.ok) throw new Error("Failed to fetch calls")
        const data = await response.json()
        setCalls(data.calls)
      } catch (error) {
        console.error("[v0] Error fetching calls:", error)
        // Use placeholder data if API fails
        setCalls([
          {
            id: "1",
            caller: "John Doe",
            phone: "+1 (555) 123-4567",
            time: "2024-12-15 14:32",
            duration: "3m 45s",
            status: "completed",
            escalated: false,
            transcript:
              "Agent: Hello, thank you for calling. How can I help you today?\nCaller: Hi, I need to schedule an appointment.\nAgent: I'd be happy to help you with that. What service are you interested in?\nCaller: I need a consultation.\nAgent: Great! Let me schedule that for you...",
            intakeData: {
              name: "John Doe",
              service: "Consultation",
              preferredDate: "2024-12-20",
              phone: "+1 (555) 123-4567",
              email: "john.doe@example.com",
            },
          },
          {
            id: "2",
            caller: "Jane Smith",
            phone: "+1 (555) 987-6543",
            time: "2024-12-15 14:17",
            duration: "2m 12s",
            status: "completed",
            escalated: true,
            transcript:
              "Agent: Hello, thank you for calling. How can I help you today?\nCaller: I have a complex issue that needs immediate attention.\nAgent: I understand. Let me connect you with a specialist right away.",
            intakeData: {
              name: "Jane Smith",
              issue: "Complex technical inquiry",
              priority: "high",
              phone: "+1 (555) 987-6543",
            },
          },
          {
            id: "3",
            caller: "Bob Johnson",
            phone: "+1 (555) 456-7890",
            time: "2024-12-15 13:45",
            duration: "4m 58s",
            status: "completed",
            escalated: false,
            transcript:
              "Agent: Hello, thank you for calling. How can I help you today?\nCaller: I wanted to ask about your business hours.\nAgent: We're open Monday through Friday, 9 AM to 5 PM...",
            intakeData: {
              name: "Bob Johnson",
              inquiry: "Business hours",
              phone: "+1 (555) 456-7890",
            },
          },
        ])
      } finally {
        setIsLoading(false)
      }
    }

    fetchCalls()
  }, [])

  const getStatusColor = (status: Call["status"]) => {
    switch (status) {
      case "completed":
        return "bg-success text-success-foreground"
      case "in_progress":
        return "bg-warning text-warning-foreground"
      case "failed":
        return "bg-destructive text-destructive-foreground"
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <Nav />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight">Call Logs</h1>
          <p className="text-muted-foreground mt-1">View and analyze voice agent call history</p>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle>All Calls</CardTitle>
              <CardDescription>Click on a call to view details</CardDescription>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="size-6 animate-spin text-muted-foreground" />
                </div>
              ) : (
                <div className="space-y-2">
                  {calls.map((call) => (
                    <button
                      key={call.id}
                      onClick={() => setSelectedCall(call)}
                      className={`w-full text-left p-4 rounded-lg border border-border hover:bg-accent transition-colors ${
                        selectedCall?.id === call.id ? "bg-accent" : ""
                      }`}
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Phone className="size-4 text-muted-foreground" />
                          <span className="font-medium">{call.caller}</span>
                        </div>
                        <Badge className={getStatusColor(call.status)}>{call.status.replace("_", " ")}</Badge>
                      </div>
                      <div className="text-sm text-muted-foreground space-y-1">
                        <p>{call.phone}</p>
                        <p>
                          {call.time} • {call.duration}
                        </p>
                      </div>
                      {call.escalated && (
                        <Badge variant="outline" className="text-warning border-warning mt-2">
                          Escalated
                        </Badge>
                      )}
                    </button>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <div className="lg:col-span-1">
            {selectedCall ? (
              <Card>
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle>{selectedCall.caller}</CardTitle>
                      <CardDescription>{selectedCall.phone}</CardDescription>
                    </div>
                    <Button variant="ghost" size="icon" onClick={() => setSelectedCall(null)}>
                      <X className="size-4" />
                    </Button>
                  </div>
                </CardHeader>
                <CardContent className="space-y-6">
                  <div>
                    <h3 className="text-sm font-semibold mb-2">Call Information</h3>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Time:</span>
                        <span>{selectedCall.time}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Duration:</span>
                        <span>{selectedCall.duration}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Status:</span>
                        <Badge className={getStatusColor(selectedCall.status)}>
                          {selectedCall.status.replace("_", " ")}
                        </Badge>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">Escalated:</span>
                        <span>{selectedCall.escalated ? "Yes" : "No"}</span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h3 className="text-sm font-semibold mb-2">Transcript</h3>
                    <div className="bg-muted rounded-lg p-4 text-sm whitespace-pre-line max-h-64 overflow-y-auto">
                      {selectedCall.transcript}
                    </div>
                  </div>

                  <div>
                    <h3 className="text-sm font-semibold mb-2">Intake Data</h3>
                    <div className="bg-muted rounded-lg p-4">
                      <pre className="text-xs font-mono overflow-x-auto">
                        {JSON.stringify(selectedCall.intakeData, null, 2)}
                      </pre>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ) : (
              <Card className="h-full flex items-center justify-center">
                <CardContent className="text-center py-12">
                  <Phone className="size-12 text-muted-foreground mx-auto mb-4" />
                  <p className="text-muted-foreground">Select a call to view details</p>
                </CardContent>
              </Card>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
