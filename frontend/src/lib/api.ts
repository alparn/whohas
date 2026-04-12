import createClient from "openapi-fetch";
import type { paths } from "./api-types";

const baseUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export const api = createClient<paths>({ baseUrl });
