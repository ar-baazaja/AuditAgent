/**
 * Validated public environment access.
 * Fails fast with a clear message if a required var is missing, instead of
 * surfacing a confusing runtime error deep in the Supabase client.
 */
function required(name: string, value: string | undefined): string {
  if (!value) {
    throw new Error(
      `Missing environment variable ${name}. Copy .env.local.example to .env.local and fill it in.`,
    );
  }
  return value;
}

export const env = {
  supabaseUrl: required(
    "NEXT_PUBLIC_SUPABASE_URL",
    process.env.NEXT_PUBLIC_SUPABASE_URL,
  ),
  supabaseAnonKey: required(
    "NEXT_PUBLIC_SUPABASE_ANON_KEY",
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
  ),
  // Optional in Phase 1 (used by the dashboard in Phase 3).
  backendUrl: process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000",
};
