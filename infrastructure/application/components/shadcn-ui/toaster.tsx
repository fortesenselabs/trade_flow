"use client"

import {
  Toast,
  ToastClose,
  ToastDescription,
  ToastProvider,
  ToastTitle,
  ToastViewport,
} from "@/components/shadcn-ui/toast"
import { useToast } from "@/components/shadcn-ui/use-toast"

/**
 * This component is responsible for rendering toast notifications.
 * @returns {JSX.Element} Toaster component
 */
export function Toaster() {
  // Extract toast state using custom hook.
  const { toasts } = useToast()

  return (
    <ToastProvider>
      {/* Map through toast array to render individual toasts. */}
      {toasts.map(function ({ id, title, description, action, ...props }) {
        return (
          <Toast key={id} {...props}>
            {/* Use grid layout for toast content. */}
            <div className="grid gap-1">
              {title && <ToastTitle>{title}</ToastTitle>}
              {description && (
                <ToastDescription>{description}</ToastDescription>
              )}
            </div>
            {action}
            {/* Render close button for the toast. */}
            <ToastClose />
          </Toast>
        )
      })}
      {/* Render toast viewport. */}
      <ToastViewport />
    </ToastProvider>
  )
}
