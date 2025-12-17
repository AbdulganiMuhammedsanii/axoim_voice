import { NextResponse } from "next/server"

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"

export async function POST(request: Request) {
  try {
    const body = await request.json()
    const orgId = body.org_id || "org_demo_001" // Default to demo org

    const response = await fetch(`${BACKEND_URL}/api/call/start`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ org_id: orgId }),
    })

    if (!response.ok) {
      const error = await response.json()
      return NextResponse.json(
        { error: error.detail || "Failed to start call" },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error("Error starting call:", error)
    return NextResponse.json(
      { error: "Failed to start call" },
      { status: 500 }
    )
  }
}
