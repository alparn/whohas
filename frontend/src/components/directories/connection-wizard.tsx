"use client";

import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { toast } from "sonner";
import { useCreateDirectory } from "@/hooks/use-directories";
import { ConnectionTestButton } from "./connection-test-button";
import type { DirectoryCreate } from "@/lib/api-types";

const schema = z.object({
  name: z.string().min(1, "Name is required"),
  host: z.string().min(1, "Server host is required"),
  port: z.number().int().min(1).max(65535),
  use_ssl: z.boolean(),
  bind_dn: z
    .string()
    .min(1, "Bind DN is required")
    .refine((v) => v.includes("="), "Must be a valid DN (e.g. CN=user,DC=corp,DC=local)"),
  bind_password: z.string().min(1, "Password is required"),
  base_dn: z
    .string()
    .min(1, "Base DN is required")
    .refine((v) => v.includes("="), "Must be a valid DN (e.g. DC=corp,DC=local)"),
  user_filter: z.string().optional(),
  group_filter: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

export function ConnectionWizard() {
  const router = useRouter();
  const createDirectory = useCreateDirectory();

  const {
    register,
    handleSubmit,
    watch,
    setValue,
    getValues,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "",
      host: "",
      port: 389,
      use_ssl: false,
      bind_dn: "",
      bind_password: "",
      base_dn: "",
      user_filter: "",
      group_filter: "",
    },
  });

  const useSsl = watch("use_ssl");

  const handleSslToggle = (checked: boolean) => {
    setValue("use_ssl", checked);
    if (checked && getValues("port") === 389) {
      setValue("port", 636);
    } else if (!checked && getValues("port") === 636) {
      setValue("port", 389);
    }
  };

  const onSubmit = (values: FormValues) => {
    const body: DirectoryCreate = { ...values };
    if (!body.user_filter) delete body.user_filter;
    if (!body.group_filter) delete body.group_filter;
    createDirectory.mutate(body, {
      onSuccess: (directory) => {
        toast.success("Directory created — starting initial sync");
        router.push(`/directories/${directory.id}`);
      },
      onError: () => {
        toast.error("Failed to create directory");
      },
    });
  };

  return (
    <Card className="w-full max-w-xl">
      <CardHeader>
        <CardTitle>Connect a directory</CardTitle>
        <CardDescription>
          Add an AD or LDAP server. whohas will sync a read-only snapshot of
          users and groups.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
          <fieldset className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Display name</Label>
              <Input
                id="name"
                placeholder='e.g. "Production AD"'
                {...register("name")}
              />
              {errors.name && (
                <p className="text-xs text-destructive">{errors.name.message}</p>
              )}
            </div>

            <div className="grid gap-4 sm:grid-cols-[1fr_100px]">
              <div className="space-y-2">
                <Label htmlFor="host">Server host</Label>
                <Input
                  id="host"
                  placeholder="ldap.corp.local"
                  {...register("host")}
                />
                {errors.host && (
                  <p className="text-xs text-destructive">{errors.host.message}</p>
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="port">Port</Label>
                <Input
                  id="port"
                  type="number"
                  {...register("port", { valueAsNumber: true })}
                />
                <div className="flex gap-1">
                  <button
                    type="button"
                    onClick={() => setValue("port", 389)}
                    className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground hover:bg-accent"
                  >
                    389
                  </button>
                  <button
                    type="button"
                    onClick={() => setValue("port", 636)}
                    className="rounded bg-muted px-1.5 py-0.5 text-[10px] font-medium text-muted-foreground hover:bg-accent"
                  >
                    636
                  </button>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <Switch
                id="use_ssl"
                checked={useSsl}
                onCheckedChange={handleSslToggle}
              />
              <Label htmlFor="use_ssl" className="cursor-pointer">
                Use SSL/TLS
              </Label>
            </div>
          </fieldset>

          <fieldset className="space-y-4">
            <TooltipProvider>
              <div className="space-y-2">
                <div className="flex items-center gap-1">
                  <Label htmlFor="bind_dn">Bind DN</Label>
                  <Tooltip>
                    <TooltipTrigger>
                      <span className="inline-flex h-4 w-4 cursor-help items-center justify-center rounded-full bg-muted text-[10px] font-medium text-muted-foreground">
                        ?
                      </span>
                    </TooltipTrigger>
                    <TooltipContent className="max-w-xs">
                      The Distinguished Name of the account used to bind to
                      LDAP, e.g. CN=svc-reader,OU=Service Accounts,DC=corp,DC=local
                    </TooltipContent>
                  </Tooltip>
                </div>
                <Input
                  id="bind_dn"
                  placeholder="CN=svc-reader,OU=Service Accounts,DC=corp,DC=local"
                  {...register("bind_dn")}
                />
                {errors.bind_dn && (
                  <p className="text-xs text-destructive">
                    {errors.bind_dn.message}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="bind_password">Bind password</Label>
                <Input
                  id="bind_password"
                  type="password"
                  {...register("bind_password")}
                />
                {errors.bind_password && (
                  <p className="text-xs text-destructive">
                    {errors.bind_password.message}
                  </p>
                )}
              </div>

              <div className="space-y-2">
                <div className="flex items-center gap-1">
                  <Label htmlFor="base_dn">Base DN</Label>
                  <Tooltip>
                    <TooltipTrigger>
                      <span className="inline-flex h-4 w-4 cursor-help items-center justify-center rounded-full bg-muted text-[10px] font-medium text-muted-foreground">
                        ?
                      </span>
                    </TooltipTrigger>
                    <TooltipContent className="max-w-xs">
                      The root of the directory tree to search, e.g.
                      DC=corp,DC=local
                    </TooltipContent>
                  </Tooltip>
                </div>
                <Input
                  id="base_dn"
                  placeholder="DC=corp,DC=local"
                  {...register("base_dn")}
                />
                {errors.base_dn && (
                  <p className="text-xs text-destructive">
                    {errors.base_dn.message}
                  </p>
                )}
              </div>
            </TooltipProvider>
          </fieldset>

          <fieldset className="space-y-4">
            <legend className="text-sm font-medium text-muted-foreground">
              LDAP Filters (optional — defaults to Active Directory)
            </legend>
            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="user_filter">User filter</Label>
                <Input
                  id="user_filter"
                  placeholder="(objectClass=user)"
                  {...register("user_filter")}
                />
                <p className="text-[11px] text-muted-foreground">
                  OpenLDAP: (objectClass=inetOrgPerson)
                </p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="group_filter">Group filter</Label>
                <Input
                  id="group_filter"
                  placeholder="(objectClass=group)"
                  {...register("group_filter")}
                />
                <p className="text-[11px] text-muted-foreground">
                  OpenLDAP: (objectClass=groupOfNames)
                </p>
              </div>
            </div>
          </fieldset>

          <div className="flex flex-col gap-3 pt-2 sm:flex-row sm:items-start sm:justify-between">
            <ConnectionTestButton
              getValues={() => getValues() as DirectoryCreate}
            />
            <Button type="submit" disabled={createDirectory.isPending}>
              {createDirectory.isPending && (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              )}
              Save and sync
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
