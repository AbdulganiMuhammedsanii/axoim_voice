"use client"

import { useState, useEffect } from "react"
import { Nav } from "@/components/nav"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Loader2, Save } from "lucide-react"

interface OrgConfig {
  organizationName: string
  businessHours: string
  servicesOffered: string
  afterHoursBehavior: string
  escalationPhone: string
}

export default function SettingsPage() {
  const [config, setConfig] = useState<OrgConfig>({
    organizationName: "",
    businessHours: "",
    servicesOffered: "",
    afterHoursBehavior: "voicemail",
    escalationPhone: "",
  })
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)

  useEffect(() => {
    // Fetch config from GET /api/org/config
    const fetchConfig = async () => {
      try {
        setIsLoading(true)
        const response = await fetch("/api/org/config")
        if (!response.ok) throw new Error("Failed to fetch config")
        const data = await response.json()
        setConfig(data)
      } catch (error) {
        console.error("[v0] Error fetching config:", error)
        // Use default values if API fails
        setConfig({
          organizationName: "Axiom Labs",
          businessHours: "Monday-Friday, 9:00 AM - 5:00 PM",
          servicesOffered: "Consultations\nTechnical Support\nProduct Inquiries\nScheduling",
          afterHoursBehavior: "voicemail",
          escalationPhone: "+1 (555) 100-2000",
        })
      } finally {
        setIsLoading(false)
      }
    }

    fetchConfig()
  }, [])

  const handleSave = async () => {
    setIsSaving(true)
    try {
      // Call POST /api/org/config
      const response = await fetch("/api/org/config", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      })

      if (!response.ok) throw new Error("Failed to save config")

      console.log("[v0] Config saved successfully")

      // Show success feedback
      await new Promise((resolve) => setTimeout(resolve, 1000))
      alert("Settings saved successfully!")
    } catch (error) {
      console.error("[v0] Error saving config:", error)
      alert("Failed to save settings. Please try again.")
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background">
        <Nav />
        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex items-center justify-center py-12">
            <Loader2 className="size-8 animate-spin text-muted-foreground" />
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-background">
      <Nav />
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold tracking-tight">Organization Settings</h1>
          <p className="text-muted-foreground mt-1">Configure your AI voice agent behavior and organization details</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Configuration</CardTitle>
            <CardDescription>Update your organization settings and agent behavior</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="orgName">Organization Name</Label>
              <Input
                id="orgName"
                value={config.organizationName}
                onChange={(e) => setConfig({ ...config, organizationName: e.target.value })}
                placeholder="Enter organization name"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="businessHours">Business Hours</Label>
              <Input
                id="businessHours"
                value={config.businessHours}
                onChange={(e) => setConfig({ ...config, businessHours: e.target.value })}
                placeholder="e.g., Monday-Friday, 9:00 AM - 5:00 PM"
              />
              <p className="text-sm text-muted-foreground">
                Define when your organization is available to handle calls
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="services">Services Offered</Label>
              <Textarea
                id="services"
                value={config.servicesOffered}
                onChange={(e) => setConfig({ ...config, servicesOffered: e.target.value })}
                placeholder="List services offered (one per line)"
                rows={6}
                className="font-mono text-sm"
              />
              <p className="text-sm text-muted-foreground">
                List all services your organization provides (one per line)
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="afterHours">After-Hours Behavior</Label>
              <Select
                value={config.afterHoursBehavior}
                onValueChange={(value) => setConfig({ ...config, afterHoursBehavior: value })}
              >
                <SelectTrigger id="afterHours">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="voicemail">Take Voicemail</SelectItem>
                  <SelectItem value="callback">Schedule Callback</SelectItem>
                  <SelectItem value="emergency">Emergency Line Only</SelectItem>
                  <SelectItem value="reject">Reject Calls</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-sm text-muted-foreground">Define how calls are handled outside business hours</p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="escalationPhone">Escalation Phone Number</Label>
              <Input
                id="escalationPhone"
                type="tel"
                value={config.escalationPhone}
                onChange={(e) => setConfig({ ...config, escalationPhone: e.target.value })}
                placeholder="+1 (555) 000-0000"
              />
              <p className="text-sm text-muted-foreground">
                Phone number for escalating complex calls to human operators
              </p>
            </div>

            <div className="pt-4 flex justify-end">
              <Button onClick={handleSave} disabled={isSaving}>
                {isSaving ? (
                  <>
                    <Loader2 className="size-4 mr-2 animate-spin" />
                    Saving...
                  </>
                ) : (
                  <>
                    <Save className="size-4 mr-2" />
                    Save Configuration
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
