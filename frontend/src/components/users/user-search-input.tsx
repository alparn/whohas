"use client";

import { Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import { useEffect, useRef } from "react";

interface UserSearchInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

export function UserSearchInput({
  value,
  onChange,
  placeholder = "Search by name, username, or email…",
}: UserSearchInputProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  return (
    <div className="relative">
      <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
      <Input
        ref={inputRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="pl-9 h-11 text-base"
      />
    </div>
  );
}
