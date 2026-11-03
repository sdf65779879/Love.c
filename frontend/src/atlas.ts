import { api } from "./api";

export interface Atlas {
  regions: { id: string; name: string; path: string }[];
  cities: { id: string; name: string; region: string; point: [number, number] }[];
  outline: string;
}

let cached: Atlas | undefined;
export async function loadAtlas() {
  if (!cached) cached = await api<Atlas>("/atlas");
  return cached;
}
