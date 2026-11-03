export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
  ) {
    super(message);
  }
}

export async function api<T = any>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...options,
    credentials: "same-origin",
    headers:
      options.body instanceof FormData
        ? options.headers
        : { "Content-Type": "application/json", ...options.headers },
  });
  if (response.status === 204) return undefined as T;
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401 && !path.startsWith("/auth/") && !path.startsWith("/visitor/") && !window.location.pathname.startsWith("/admin") && window.location.pathname !== "/login" && window.location.pathname !== "/enter") {
      window.location.replace("/enter");
    }
    const message = Array.isArray(data.detail)
      ? data.detail
          .map((error: any) => error.msg.replace("Value error, ", ""))
          .join("；")
      : data.detail;
    throw new ApiError(
      message || "请求暂时未完成，请稍后重试",
      response.status,
    );
  }
  return data as T;
}

export interface Entry {
  id: number;
  title: string;
  content?: string;
  excerpt?: string;
  author?: string;
  cover?: string;
  image?: string;
  date?: string;
  location?: string;
  city_id?: string;
  annual?: boolean;
  elapsed_days?: number;
  days_until?: number | null;
  next_date?: string | null;
  completed?: boolean;
  description?: string;
  sender?: string;
  published?: boolean;
  name?: string;
  approved?: boolean;
  created_at?: string;
}
export interface Page {
  items: Entry[];
  total: number;
  page: number;
  page_size: number;
}
export async function allMemories(kind: "places" | "anniversaries"): Promise<Entry[]> {
  const items: Entry[] = [];
  for (let page = 1; ; page++) {
    const batch = await api<Page>(`/content/${kind}?page=${page}&page_size=100`);
    items.push(...batch.items);
    if (items.length >= batch.total || !batch.items.length) return items;
  }
}
export const write = (method: string, data: unknown): RequestInit => ({
  method,
  body: JSON.stringify(data),
});
export const dateLabel = (value?: string) => {
  if (!value) return "";
  if (!value.includes("T")) return value.replaceAll("-", ".");
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "Asia/Shanghai",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  })
    .format(new Date(value))
    .replaceAll("-", ".");
};
