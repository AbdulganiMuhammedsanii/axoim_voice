import { NextResponse } from "next/server"

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const callId = body.call_id

    if (!callId) {
      return NextResponse.json(
        { error: "call_id is required" },
        { status: 400 }
      )
    }

    const response = await fetch(`${BACKEND_URL}/api/call/end`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ call_id: callId }),
    })

    if (!response.ok) {
      const error = await response.json()
      return NextResponse.json(
        { error: error.detail || "Failed to end call" },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error("Error ending call:", error)
    return NextResponse.json(
      { error: "Failed to end call" },
      { status: 500 }
    )
  }
}

