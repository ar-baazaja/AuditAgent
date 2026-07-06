import { redirect } from "next/navigation";

import { createClient } from "@/lib/supabase/server";

/**
 * The product lives at /dashboard. Middleware (src/middleware.ts) sends
 * unauthenticated visitors to /login.
 *
 * This also defensively handles a Supabase auth `?code=` landing here
 * instead of /auth/callback — which happens if the Supabase project's Site
 * URL (Authentication -> URL Configuration) is misconfigured to the app
 * root rather than /auth/callback. Exchanging it here means email
 * confirmation still works even before that dashboard setting is fixed.
 */
export default async function Home({
  searchParams,
}: {
  searchParams: Promise<{ code?: string }>;
}) {
  const { code } = await searchParams;

  if (code) {
    const supabase = await createClient();
    const { error } = await supabase.auth.exchangeCodeForSession(code);
    if (error) {
      redirect(`/login?error=${encodeURIComponent(error.message)}`);
    }
  }

  redirect("/dashboard");
}
