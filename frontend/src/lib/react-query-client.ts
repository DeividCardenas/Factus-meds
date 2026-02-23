import { QueryClient } from "@tanstack/react-query";

export const API_BASE_URL = "http://localhost:8080/api/v1";

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60,
      retry: 1,
    },
  },
});
