import { AlertCircle, CheckCircle2, Info, X } from "lucide-react";
import { createContext, useCallback, useContext, useState } from "react";
import { cn } from "@/common/utils";

type ToastType = "success" | "error" | "info";

interface Toast {
	id: number;
	type: ToastType;
	message: string;
}

interface ToastContextValue {
	toasts: Toast[];
	toast: (type: ToastType, message: string) => void;
	dismiss: (id: number) => void;
}

const ToastContext = createContext<ToastContextValue>({
	toasts: [],
	toast: () => {},
	dismiss: () => {},
});

let _nextId = 0;

export function ToastProvider({ children }: { children: React.ReactNode }) {
	const [toasts, setToasts] = useState<Toast[]>([]);

	const dismiss = useCallback((id: number) => {
		setToasts((prev) => prev.filter((t) => t.id !== id));
	}, []);

	const toast = useCallback(
		(type: ToastType, message: string) => {
			const id = ++_nextId;
			setToasts((prev) => [...prev, { id, type, message }]);
			setTimeout(() => dismiss(id), 5000);
		},
		[dismiss],
	);

	return (
		<ToastContext.Provider value={{ toasts, toast, dismiss }}>
			{children}
			<div className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm">
				{toasts.map((t) => (
					<div
						key={t.id}
						className={cn(
							"flex items-start gap-2 px-4 py-3 rounded-lg border shadow-lg text-sm animate-in slide-in-from-right-full",
							t.type === "success" &&
								"bg-emerald-950/90 border-emerald-800 text-emerald-300",
							t.type === "error" && "bg-red-950/90 border-red-800 text-red-300",
							t.type === "info" &&
								"bg-blue-950/90 border-blue-800 text-blue-300",
						)}
					>
						{t.type === "success" && (
							<CheckCircle2 className="h-4 w-4 mt-0.5 shrink-0" />
						)}
						{t.type === "error" && (
							<AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
						)}
						{t.type === "info" && <Info className="h-4 w-4 mt-0.5 shrink-0" />}
						<span className="flex-1">{t.message}</span>
						<button
							type="button"
							onClick={() => dismiss(t.id)}
							className="shrink-0 hover:opacity-70"
						>
							<X className="h-3.5 w-3.5" />
						</button>
					</div>
				))}
			</div>
		</ToastContext.Provider>
	);
}

export function useToast() {
	return useContext(ToastContext);
}
