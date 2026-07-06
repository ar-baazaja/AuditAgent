import { redirect } from "next/navigation";

/**
 * The product now lives at /dashboard. Middleware (src/middleware.ts) sends
 * unauthenticated visitors to /login, so this redirect is safe for both
 * signed-in and signed-out users.
 */
export default function Home() {
  redirect("/dashboard");
}
