# Switching Network OS

With the group-based topology, switching between network operating systems is simple.

## How It Works

The topology defines groups with default settings:

```yaml
groups:
  frr-router:
    image: frrouting/frr:latest
  sonic-router:
    image: docker-sonic-vs:latest
```

All routers inherit from a group:
```yaml
spine1:
  group: frr-router
  mgmt-ipv4: 172.20.20.10
  binds:
    - ./frr/spine1:/etc/frr
```

## Switch Individual Router to SONiC

Edit `topology.yml` and change the group and binds:

```yaml
spine1:
  group: sonic-router     # Changed from frr-router
  mgmt-ipv4: 172.20.20.10
  binds:
    - ./sonic/spine1:/etc/sonic  # Changed path
```

Then redeploy:
```bash
./lab restart
```

## Switch All Routers to SONiC

Edit the group definition in `topology.yml`:

```yaml
groups:
  frr-router:
    image: docker-sonic-vs:latest  # Changed from frrouting/frr:latest
```

And update all binds from `./frr/` to `./sonic/` and `/etc/frr` to `/etc/sonic`.

## Mix and Match

You can run some routers as FRR and others as SONiC:

```yaml
spine1:
  group: sonic-router    # SONiC
  binds:
    - ./sonic/spine1:/etc/sonic

spine2:
  group: frr-router      # FRR
  binds:
    - ./frr/spine2:/etc/frr
```

## Benefits

✅ Group-based inheritance (proper ContainerLab way)  
✅ Easy to switch individual nodes or all nodes  
✅ Mix different NOS in same topology  
✅ Clean and maintainable  

## Note

- FRR works on ARM64 (Apple Silicon)
- SONiC requires x86_64 architecture
- Remember to update both `group` and `binds` when switching
