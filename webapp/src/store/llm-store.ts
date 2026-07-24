import { create } from "zustand";

export type Provider = {
  id: string;
  name: string;
  endpoint: string | null;
  available: boolean | null;
  models: string[];
};

type GpuInfo = {
  detected: boolean;
  name?: string;
  vram?: string;
  driver?: string;
};

type LlmStore = {
  providers: Provider[];
  gpu: GpuInfo;
  selectedProvider: string;
  selectedModel: string;
  loading: boolean;

  setProviders: (providers: Provider[], gpu: GpuInfo) => void;
  setSelectedProvider: (id: string) => void;
  setSelectedModel: (model: string) => void;
  setLoading: (loading: boolean) => void;
};

export const useLlmStore = create<LlmStore>((set) => ({
  providers: [],
  gpu: { detected: false },
  selectedProvider: localStorage.getItem("llm_provider") || "",
  selectedModel: localStorage.getItem("llm_model") || "",
  loading: true,

  setProviders: (providers, gpu) => set({ providers, gpu, loading: false }),
  setSelectedProvider: (id) => {
    localStorage.setItem("llm_provider", id);
    set({ selectedProvider: id, selectedModel: "" });
  },
  setSelectedModel: (model) => {
    localStorage.setItem("llm_model", model);
    set({ selectedModel: model });
  },
  setLoading: (loading) => set({ loading }),
}));
