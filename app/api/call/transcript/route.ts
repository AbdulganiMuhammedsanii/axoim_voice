import { NextResponse } from "next/server"

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000"

export async function POST(request: Request) {
  try {
    const body = await request.json()

    const response = await fetch(`${BACKEND_URL}/api/call/transcript`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      const error = await response.json()
      return NextResponse.json(
        { error: error.detail || "Failed to save transcript" },
        { status: response.status }
      )
    }

    const data = await response.json()
    return NextResponse.json(data)
  } catch (error) {
    console.error("Error saving transcript:", error)
    return NextResponse.json(
      { error: "Failed to save transcript" },
      { status: 500 }
    )
  }
}

