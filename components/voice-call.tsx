"use client"

import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Phone, PhoneOff, Mic, MicOff, Loader2 } from "lucide-react"
import { Badge } from "@/components/ui/badge"

interface VoiceCallProps {
  orgId?: string
  onCallEnd?: () => void
}

export function VoiceCall({ orgId = "org_demo_001", onCallEnd }: VoiceCallProps) {
  const [callId, setCallId] = useState<string | null>(null)
  const [session, setSession] = useState<{ session_id: string; client_secret: string } | null>(null)
  const [isConnecting, setIsConnecting] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [isRecording, setIsRecording] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [transcript, setTranscript] = useState<Array<{ speaker: string; text: string }>>([])
  const [audioInputActive, setAudioInputActive] = useState(false)
  const [audioOutputActive, setAudioOutputActive] = useState(false)

  const wsRef = useRef<WebSocket | null>(null)
  const audioContextRef = useRef<AudioContext | null>(null)
  const mediaStreamRef = useRef<MediaStream | null>(null)

  const startCall = async () => {
    try {
      setIsConnecting(true)
      setError(null)

      // 1. Start call
      const callResponse = await fetch("/api/call/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ org_id: orgId }),
      })

      if (!callResponse.ok) {
        throw new Error("Failed to start call")
      }

      const callData = await callResponse.json()
      setCallId(callData.call_id)

      // 2. Create Realtime session
      const sessionResponse = await fetch("/api/realtime/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ org_id: orgId }),
      })

      if (!sessionResponse.ok) {
        throw new Error("Failed to create session")
      }

      const sessionData = await sessionResponse.json()
      setSession(sessionData)

      // 3. Connect to OpenAI Realtime API
      await connectToRealtime(sessionData)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start call")
      setIsConnecting(false)
    }
  }

  const connectToRealtime = async (sessionData: { session_id: string; client_secret: string; session_config?: any }) => {
    try {
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          sampleRate: 24000,
          channelCount: 1,
          echoCancellation: true,
          noiseSuppression: true,
        },
      })

      mediaStreamRef.current = stream

      // Create audio context for input
      const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)({
        sampleRate: 24000,
      })
      audioContextRef.current = audioContext

      // Create audio context for output (separate from input)
      const outputAudioContext = new (window.AudioContext || (window as any).webkitAudioContext)({
        sampleRate: 24000,
      })

      // Connect to OpenAI Realtime API via backend WebSocket proxy
      // Pass the ephemeral key (client_secret) as query parameter
      const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"
      const wsUrl = `${backendUrl.replace("http://", "ws://").replace("https://", "wss://")}/api/realtime/ws?client_secret=${encodeURIComponent(sessionData.client_secret)}`
      
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws

      // Audio buffer for output
      let audioBufferQueue: Float32Array[] = []
      let isPlaying = false

      const playAudio = async (audioData: Float32Array) => {
        if (audioData.length === 0) return
        
        setAudioOutputActive(true)
        
        if (isPlaying) {
          audioBufferQueue.push(audioData)
          return
        }

        isPlaying = true
        
        try {
          // Resume audio context if suspended (browser autoplay policy)
          if (outputAudioContext.state === 'suspended') {
            await outputAudioContext.resume()
          }
          
          const buffer = outputAudioContext.createBuffer(1, audioData.length, 24000)
          const channelData = buffer.getChannelData(0)
          channelData.set(audioData)
          const source = outputAudioContext.createBufferSource()
          source.buffer = buffer
          source.connect(outputAudioContext.destination)
          
          source.onended = () => {
            isPlaying = false
            if (audioBufferQueue.length > 0) {
              playAudio(audioBufferQueue.shift()!)
            } else {
              setAudioOutputActive(false)
            }
          }
          
          source.start(0)
        } catch (err) {
          console.error("Error playing audio:", err)
          isPlaying = false
          setAudioOutputActive(false)
        }
      }

      ws.onopen = () => {
        console.log("WebSocket connected")
        
        // Send session.update with full configuration (instructions + tools)
        // This must be sent after WebSocket connection is established
        if (sessionData.session_config) {
          // GA API format - minimal required fields based on docs
          const updatePayload = {
            type: "session.update",
            session: {
              type: "realtime",
              instructions: sessionData.session_config.instructions,
              tools: sessionData.session_config.tools,
              tool_choice: "auto"
            }
          }
          console.log("📤 Sending session.update")
          console.log("📤 Instructions length:", sessionData.session_config.instructions?.length)
          console.log("📤 Tools being sent:", sessionData.session_config.tools?.map((t: any) => t.name))
          ws.send(JSON.stringify(updatePayload))
        } else {
          console.error("❌ No session_config received from backend!")
        }

        // Start sending audio input
        // Using ScriptProcessorNode (deprecated but works everywhere)
        // TODO: Migrate to AudioWorkletNode for better performance
        const source = audioContext.createMediaStreamSource(stream)
        const processor = audioContext.createScriptProcessor(4096, 1, 1)

        processor.onaudioprocess = (e) => {
          if (ws.readyState === WebSocket.OPEN) {
            const inputData = e.inputBuffer.getChannelData(0)
            
            // Check if there's actual audio input (not silence)
            const hasAudio = inputData.some(sample => Math.abs(sample) > 0.01)
            setAudioInputActive(hasAudio)
            
            // Convert Float32 to Int16 PCM
            const pcm16 = new Int16Array(inputData.length)
            for (let i = 0; i < inputData.length; i++) {
              const s = Math.max(-1, Math.min(1, inputData[i]))
              pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
            }

            // Convert Int16Array to base64-encoded string
            // OpenAI Realtime API expects audio as base64-encoded bytes
            const bytes = new Uint8Array(pcm16.buffer)
            const binaryString = String.fromCharCode.apply(null, Array.from(bytes))
            const base64Audio = btoa(binaryString)

            // Send audio to OpenAI as base64-encoded string
            ws.send(JSON.stringify({
              type: "input_audio_buffer.append",
              audio: base64Audio
            }))
          }
        }

        source.connect(processor)
        processor.connect(audioContext.destination)
        
        // Store processor ref for cleanup
        ;(audioContextRef.current as any).processor = processor

        setIsConnected(true)
        setIsRecording(true)
        setIsConnecting(false)

        setTranscript((prev) => [
          ...prev,
          { speaker: "system", text: "Connected to AI agent. You can start speaking now." }
        ])
      }

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          console.log("📨 Received message:", message.type, message)
          
          // Log ALL messages to see what we're actually receiving
          // This will help us identify the correct function call event name
          if (message.type?.includes("function") || 
              message.type?.includes("tool") ||
              message.type?.includes("output_item") ||
              message.function_call ||
              message.tool_call ||
              message.item?.type === "function_call") {
            console.log("🔧 POTENTIAL FUNCTION/TOOL CALL:", JSON.stringify(message, null, 2))
          }

          switch (message.type) {
            case "session.created":
            case "session.updated":
              // GA API uses session.updated after session.update
              console.log("Session created/updated:", message.session)
              // Trigger the AI to start speaking by creating a response
              // The AI should auto-greet, but we can also explicitly request a response
              // Don't need to explicitly create response - agent will auto-respond
              // The session.update already has instructions to greet the caller
              console.log("Session ready - agent should auto-greet")
              break

            case "conversation.item.input_audio_transcription.completed":
              // User speech transcribed
              const userTranscript = { speaker: "user", text: message.transcript }
              setTranscript((prev) => [...prev, userTranscript])
              
              // Save transcript to database in real-time
              if (callId) {
                fetch("/api/call/transcript", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                    call_id: callId,
                    speaker: "user",
                    text: message.transcript,
                  }),
                }).catch(err => console.error("Failed to save user transcript:", err))
              }
              break

            case "response.output_audio_transcript.done":
              // Agent speech transcribed (GA API event name)
              const agentTranscript = { speaker: "agent", text: message.transcript }
              setTranscript((prev) => [...prev, agentTranscript])
              
              // Save transcript to database in real-time
              if (callId) {
                fetch("/api/call/transcript", {
                  method: "POST",
                  headers: { "Content-Type": "application/json" },
                  body: JSON.stringify({
                    call_id: callId,
                    speaker: "agent",
                    text: message.transcript,
                  }),
                }).catch(err => console.error("Failed to save agent transcript:", err))
              }
              break

            case "response.output_audio.delta":
              // Audio output from agent (GA API event name)
              if (message.delta) {
                try {
                  // Decode base64 audio to Float32Array
                  const binaryString = atob(message.delta)
                  const bytes = new Uint8Array(binaryString.length)
                  for (let i = 0; i < binaryString.length; i++) {
                    bytes[i] = binaryString.charCodeAt(i)
                  }
                  
                  // Convert Int16 PCM to Float32
                  // Note: bytes.buffer might not align correctly, so we need to handle this properly
                  const int16View = new DataView(bytes.buffer)
                  const float32Array = new Float32Array(bytes.length / 2)
                  for (let i = 0; i < float32Array.length; i++) {
                    const int16 = int16View.getInt16(i * 2, true) // little-endian
                    float32Array[i] = int16 / 32768.0
                  }
                  
                  if (float32Array.length > 0) {
                    playAudio(float32Array)
                  }
                } catch (err) {
                  console.error("Error processing audio delta:", err)
                }
              }
              break

            case "response.function_call_arguments.done":
            case "response.output_item.done":
              // Tool call from agent - GA API format
              // Log the full message to understand the structure
              console.log("📦 Full function call message:", JSON.stringify(message, null, 2))
              
              let functionCall = null
              let callIdForTool = null
              
              // GA API: function call comes in response.output_item.done with item.type = "function_call"
              if (message.item && message.item.type === "function_call") {
                // The function call details are directly on the item
                functionCall = {
                  name: message.item.name,
                  arguments: message.item.arguments || "{}"
                }
                // CRITICAL: The call_id is on the item itself, NOT item.id
                // item.id is the conversation item ID
                // item.call_id is what we need to reference when returning the output
                callIdForTool = message.item.call_id || message.item.id
                
                console.log("🔧 Extracted function call:", {
                  name: functionCall.name,
                  call_id: callIdForTool,
                  item_id: message.item.id
                })
              }
              
              // Parse arguments if they're a string (JSON)
              if (functionCall && typeof functionCall.arguments === "string") {
                try {
                  functionCall.arguments = JSON.parse(functionCall.arguments)
                } catch (e) {
                  console.warn("⚠️ Failed to parse function call arguments:", e)
                  functionCall.arguments = {}
                }
              }
              
              if (functionCall && functionCall.name && callIdForTool) {
                console.log("🔧 Processing function call:", functionCall.name, "with call_id:", callIdForTool)
                handleToolCall(functionCall, callIdForTool)
              } else if (message.item?.type !== "message") {
                // Log for debugging - we received an output_item.done but it wasn't a function call
                console.log("ℹ️ output_item.done received (not a function call):", message.item?.type)
              }
              break

            case "response.done":
              console.log("Response done")
              break

            case "error":
              const errorMsg = message.error?.message || "WebSocket error"
              const errorCode = message.error?.code || "unknown"
              const errorType = message.error?.type || "unknown"
              console.error("🚨 OpenAI API error:", {
                message: errorMsg,
                code: errorCode,
                type: errorType,
                full_error: message.error
              })
              setError(`${errorMsg} (${errorCode})`)
              setIsConnecting(false)
              break
              
            default:
              // Log unhandled message types for debugging
              if (message.type && !message.type.startsWith("input_audio_buffer")) {
                console.log("📩 Unhandled message type:", message.type)
              }
          }
        } catch (err) {
          console.error("Error parsing message:", err)
        }
      }

      ws.onerror = (error) => {
        console.error("WebSocket error:", error)
        setError("Connection error. Make sure the backend is running and has a valid OpenAI API key configured.")
        setIsConnecting(false)
      }

      ws.onclose = () => {
        console.log("WebSocket closed")
        setIsConnected(false)
        setIsRecording(false)
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to connect")
      setIsConnecting(false)
    }
  }

  const submitToolResult = (callId: string, result: any, isError: boolean = false) => {
    const ws = wsRef.current
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      console.error("Cannot submit tool result: WebSocket not connected")
      return
    }

    try {
      // Submit tool result to OpenAI Realtime API
      // The output should be a JSON string
      const output = isError 
        ? JSON.stringify({ error: result }) 
        : JSON.stringify(result)
      
      // GA API format: conversation.item.create with function_call_output
      const toolResultMessage = {
        type: "conversation.item.create",
        item: {
          type: "function_call_output",
          call_id: callId,
          output: output,
        }
      }
      
      console.log("📤 Submitting tool result to OpenAI:", { callId, output: output.substring(0, 200), isError })
      ws.send(JSON.stringify(toolResultMessage))
      
      // After submitting the function output, trigger a response
      ws.send(JSON.stringify({
        type: "response.create"
      }))
      
      console.log("✅ Tool result submitted and response triggered")
    } catch (error) {
      console.error("❌ Failed to submit tool result:", error)
    }
  }

  /**
   * Handle tool calls from OpenAI Realtime with robust pipeline.
   * 
   * WHY THIS ARCHITECTURE:
   * 1. All scheduling intents go through server-side validation
   * 2. Zapier is ONLY called from the server (CORS/security)
   * 3. Idempotency prevents duplicate calendar events on reconnects
   * 4. Structured errors prompt the model to ask for clarification
   */
  const handleToolCall = async (functionCall: any, itemId: string) => {
    const { name, arguments: args } = functionCall
    console.log("🔧 Tool call received:", name)
    console.log("   Arguments:", JSON.stringify(args, null, 2))
    console.log("   Item ID:", itemId)

    // Track execution to prevent duplicates (client-side check)
    const intentKey = `${name}_${JSON.stringify(args)}`
    
    if (name === "create_appointment") {
      // CRITICAL: Use the robust server-side pipeline for appointments
      // This ensures validation, idempotency, and proper Zapier execution
      try {
        // Show pending status
        setTranscript((prev) => [
          ...prev,
          { speaker: "system", text: `📅 Processing appointment request...` }
        ])
        
        console.log("📤 Sending to execute-intent endpoint")
        
        // Call the server-side execution pipeline
        // This handles: validation → idempotency check → Zapier webhook
        const response = await fetch("/api/execute-intent", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            tool_name: name,
            tool_args: args,
            call_id: callId,
            org_id: orgId,
            item_id: itemId,
          }),
        })
        
        const result = await response.json()
        console.log("📥 Execute-intent response:", result)
        
        if (result.success) {
          // Success - appointment created and Zapier executed
          const successMsg = result.is_duplicate
            ? `ℹ️ This appointment was already created.`
            : `✅ Appointment created! Confirmation sent to ${result.result_data?.attendee_email || args.attendee_email}`
          
          setTranscript((prev) => [
            ...prev,
            { speaker: "system", text: successMsg }
          ])
          
          // Submit success result to OpenAI Realtime
          submitToolResult(itemId, {
            success: true,
            message: result.message,
            appointment_id: result.appointment_id,
            calendar_link: result.calendar_link,
            email_sent: result.email_sent,
            is_duplicate: result.is_duplicate,
          })
        } else {
          // Failure - validation error or Zapier error
          const errorMsg = result.error || "Failed to create appointment"
          
          console.error("❌ Execute-intent failed:", result)
          
          setTranscript((prev) => [
            ...prev,
            { speaker: "system", text: `❌ ${errorMsg}` }
          ])
          
          // Submit error to OpenAI Realtime
          // If should_retry is true, include clarification for the model
          if (result.should_retry && result.clarification) {
            submitToolResult(itemId, {
              error: result.clarification,
              missing_fields: result.missing_fields,
            }, true)
          } else {
            submitToolResult(itemId, { error: errorMsg }, true)
          }
        }
      } catch (error) {
        console.error("❌ Error calling execute-intent:", error)
        const errorMsg = error instanceof Error ? error.message : 'Unknown error'
        
        setTranscript((prev) => [
          ...prev,
          { speaker: "system", text: `❌ Failed to process: ${errorMsg}` }
        ])
        
        submitToolResult(itemId, { 
          error: "Failed to process appointment. Please try again.",
        }, true)
      }
    } else if (name === "escalate_call") {
      // Escalation doesn't need Zapier - handle immediately
      setTranscript((prev) => [
        ...prev,
        { speaker: "system", text: `⚠️ Escalation requested: ${args.summary || args.reason}` }
      ])
      submitToolResult(itemId, { success: true, message: "Call escalated" })
    } else if (name === "complete_intake") {
      // Intake completion doesn't need Zapier - handle immediately
      setTranscript((prev) => [
        ...prev,
        { speaker: "system", text: "✅ Intake completed successfully" }
      ])
      submitToolResult(itemId, { success: true, message: "Intake completed" })
    } else if (name === "end_call") {
      setTranscript((prev) => [
        ...prev,
        { speaker: "system", text: "Call ending..." }
      ])
      submitToolResult(itemId, { success: true, message: "Call ended" })
      await endCall()
    } else {
      // Unknown tool call
      console.warn("⚠️ Unknown tool call:", name)
      submitToolResult(itemId, { error: `Unknown tool: ${name}` }, true)
    }
  }

  const endCall = async () => {
    try {
      if (callId) {
        await fetch("/api/call/end", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ call_id: callId }),
        })
      }

      // Cleanup
      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }

      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach((track) => track.stop())
        mediaStreamRef.current = null
      }

      if (audioContextRef.current) {
        // Disconnect processor if it exists
        const processor = (audioContextRef.current as any).processor
        if (processor) {
          processor.disconnect()
        }
        await audioContextRef.current.close()
        audioContextRef.current = null
      }

      setCallId(null)
      setSession(null)
      setIsConnected(false)
      setIsRecording(false)
      setTranscript([])

      if (onCallEnd) {
        onCallEnd()
      }
    } catch (err) {
      console.error("Error ending call:", err)
    }
  }

  useEffect(() => {
    return () => {
      // Cleanup on unmount
      if (wsRef.current) wsRef.current.close()
      if (mediaStreamRef.current) {
        mediaStreamRef.current.getTracks().forEach((track) => track.stop())
      }
      if (audioContextRef.current) {
        audioContextRef.current.close()
      }
    }
  }, [])

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          Voice Call
          {isConnected && (
            <Badge className="bg-success text-success-foreground">
              <Mic className="size-3 mr-1" />
              Connected
            </Badge>
          )}
        </CardTitle>
        <CardDescription>
          {callId ? `Call ID: ${callId}` : "Start a voice call with the AI agent"}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <div className="p-3 bg-destructive/10 text-destructive rounded-md text-sm">
            {error}
          </div>
        )}

        {session && (
          <div className="p-3 bg-muted rounded-md text-sm space-y-1">
            <div>
              <strong>Session ID:</strong> {session.session_id.substring(0, 20)}...
            </div>
            <div>
              <strong>Client Secret:</strong> {session.client_secret.substring(0, 20)}...
            </div>
          </div>
        )}

        {transcript.length > 0 && (
          <div className="p-3 bg-muted rounded-md max-h-48 overflow-y-auto space-y-2">
            {transcript.map((item, idx) => (
              <div key={idx} className="text-sm">
                <strong className="capitalize">{item.speaker}:</strong> {item.text}
              </div>
            ))}
          </div>
        )}

        <div className="flex gap-2">
          {!isConnected ? (
            <Button
              onClick={startCall}
              disabled={isConnecting}
              className="flex-1"
            >
              {isConnecting ? (
                <>
                  <Loader2 className="size-4 mr-2 animate-spin" />
                  Connecting...
                </>
              ) : (
                <>
                  <Phone className="size-4 mr-2" />
                  Start Call
                </>
              )}
            </Button>
          ) : (
            <Button
              onClick={endCall}
              variant="destructive"
              className="flex-1"
            >
              <PhoneOff className="size-4 mr-2" />
              End Call
            </Button>
          )}
        </div>

        {isRecording && (
          <div className="space-y-2">
            <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
              <Mic className={`size-4 ${audioInputActive ? 'animate-pulse text-primary' : ''}`} />
              {audioInputActive ? "Listening..." : "Microphone ready"}
            </div>
            {audioOutputActive && (
              <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground">
                <Phone className="size-4 animate-pulse text-primary" />
                AI is speaking...
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

