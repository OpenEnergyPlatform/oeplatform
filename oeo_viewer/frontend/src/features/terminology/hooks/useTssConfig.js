export function useTssConfig() {
  // could be extended to include auth headers, selected ontologies, etc.
  return {
    apiBase: import.meta.env.VITE_TSS_API_BASE || "",
  };
}
