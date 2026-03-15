export function parseApiError(error: unknown): string {
  // Handle errors with a `body` property containing backend error detail
  if (
    error != null &&
    typeof error === "object" &&
    "body" in error &&
    error.body != null
  ) {
    const body = error.body as Record<string, unknown>;
    if (typeof body.detail === "string") {
      return body.detail;
    }
    if (Array.isArray(body.detail) && body.detail.length > 0) {
      const first = body.detail[0] as { msg?: string };
      if (typeof first.msg === "string") {
        return first.msg;
      }
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "An unexpected error occurred";
}
