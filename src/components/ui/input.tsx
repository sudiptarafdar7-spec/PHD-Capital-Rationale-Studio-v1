import * as React from "react";

import { cn } from "./utils";

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        "file:text-foreground placeholder:text-muted-foreground selection:bg-primary selection:text-primary-foreground backdrop-blur-sm border-input flex h-10 w-full min-w-0 rounded-lg border px-4 py-2.5 text-base bg-input-background transition-smooth outline-none file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50 md:text-sm shadow-sm",
        "hover:border-input-hover",
        "focus-visible:border-ring focus-visible:ring-4 focus-visible:ring-input-focus focus-visible:shadow-md",
        "aria-invalid:ring-destructive-glow aria-invalid:border-destructive",
        className,
      )}
      {...props}
    />
  );
}

export { Input };
