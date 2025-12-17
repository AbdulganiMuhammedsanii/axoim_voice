/**
 * Execute Intent API Route
 * 
 * Proxies tool execution requests to the backend.
 * 
 * WHY THIS EXISTS:
 * - Next.js API routes proxy to FastAPI backend
 * - Keeps frontend code simple
 * - Allows adding client-side logging/metrics
 */

import { NextResponse } from "next/server"

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"

export async function POST(request: Request) {
  try {
    const body = await request.json()
    
    console.log("[execute-intent] Proxying request:", {
      tool_name: body.tool_name,
      call_id: body.call_id,
    })

    const response = await fetch(`${BACKEND_URL}/api/execute-intent`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const error = await response.json()
      console.error("[execute-intent] Backend error:", error)
      return NextResponse.json(
        { 
          success: false,
          error: error.detail || "Failed to execute intent",
          should_retry: true,
        },
        { status: response.status }
      )
    }

    const data = await response.json()
    console.log("[execute-intent] Success:", {
      success: data.success,
      appointment_id: data.appointment_id,
    })
    
    return NextResponse.json(data)
  } catch (error) {
    console.error("[execute-intent] Error:", error)
    return NextResponse.json(
      { 
        success: false,
        error: "Failed to execute intent",
        should_retry: true,
      },
      { status: 500 }
    )
  }
}

export async function GET() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/execute-intent/stats`, {
      method: "GET",
      headers: {
        "Content-Type": "application/json",
      },
    })

    if (!response.ok) {
      return NextResponse.json(
        { error: "Failed to get stats" },
        { status: response.status }
      )
    }

    return NextResponse.json(await response.json())
  } catch (error) {
    console.error("[execute-intent] Stats error:", error)
    return NextResponse.json(
      { error: "Failed to get stats" },
      { status: 500 }
    )
  }
}

