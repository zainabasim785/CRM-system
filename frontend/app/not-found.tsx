import { Button } from "@/components/ui/button";
import Link from "next/link";

export default function NotFound() {
  return (
    <div className="flex flex-col items-center gap-4 py-24 text-center">
      <h1 className="font-display text-3xl font-semibold">Page not found</h1>
      <Button asChild>
        <Link href="/">Back home</Link>
      </Button>
    </div>
  );
}
