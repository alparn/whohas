import { ConnectionWizard } from "@/components/directories/connection-wizard";

export default function NewDirectoryPage() {
  return (
    <div className="flex min-h-svh items-center justify-center bg-muted/30 p-6">
      <ConnectionWizard />
    </div>
  );
}
