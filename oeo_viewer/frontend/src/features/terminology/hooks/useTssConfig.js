import { useTssConfigCtx } from "../config/TssConfigProvider";

export function useTssConfig() {
  // later you can read from env and merge, but for now just return the ctx
  return useTssConfigCtx();
}
