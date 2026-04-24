import * as React from "react"

import { cn } from "@/lib/utils"

type ScrollOrientation = "vertical" | "horizontal" | "both"

function viewportOverflowClasses(orientation: ScrollOrientation) {
  switch (orientation) {
    case "horizontal":
      return "overflow-x-auto overflow-y-hidden"
    case "both":
      return "overflow-auto"
    case "vertical":
    default:
      return "overflow-y-auto overflow-x-hidden"
  }
}

const ScrollArea = React.forwardRef<
  HTMLDivElement,
  React.ComponentProps<"div"> & { orientation?: ScrollOrientation }
>(function ScrollArea(
  {
    className,
    children,
    orientation = "vertical",
    ...props
  },
  ref,
) {
  return (
    <div
      ref={ref}
      data-slot="scroll-area"
      className={cn("relative min-w-0 overflow-hidden", className)}
      {...props}
    >
      <div
        data-slot="scroll-area-viewport"
        data-radix-scroll-area-viewport=""
        className={cn(
          "focus-visible:ring-ring/50 size-full min-w-0 rounded-[inherit] transition-[color,box-shadow] outline-none focus-visible:ring-[3px] focus-visible:outline-1",
          viewportOverflowClasses(orientation),
        )}
      >
        <div className="block min-w-0 w-full">
          {children}
        </div>
      </div>
    </div>
  )
})

const ScrollBar = React.forwardRef<
  HTMLDivElement,
  React.ComponentProps<"div"> & { orientation?: Exclude<ScrollOrientation, "both"> }
>(function ScrollBar(
  {
    className,
    orientation = "vertical",
    ...props
  },
  ref,
) {
  return (
    <div
      ref={ref}
      aria-hidden="true"
      data-slot="scroll-area-scrollbar"
      className={cn(
        "pointer-events-none absolute opacity-0",
        orientation === "vertical" ? "right-0 top-0 h-full w-2.5" : "bottom-0 left-0 h-2.5 w-full",
        className,
      )}
      {...props}
    />
  )
})

ScrollArea.displayName = "ScrollArea"
ScrollBar.displayName = "ScrollBar"

export { ScrollArea, ScrollBar }
