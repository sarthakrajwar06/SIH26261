# Routes

The executable route tree is in `src/main.tsx` and uses React Router. `layouts/Shell.tsx` owns role-aware navigation; the frontend only gates navigation/convenience. FastAPI and Supabase RLS remain the security boundary.
