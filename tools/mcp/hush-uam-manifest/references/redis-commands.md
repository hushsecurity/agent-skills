# Redis Privilege Commands

Complete list of valid command names for the `command` `type` in a Redis privilege grant entry. Use lowercase. For broader access, prefer `type: category` from the [valid categories list](#categories) at the bottom of this document.

## String

- `append`
- `decr`
- `decrby`
- `get`
- `getdel`
- `getex`
- `getrange`
- `getset`
- `incr`
- `incrby`
- `incrbyfloat`
- `mget`
- `mset`
- `msetnx`
- `psetex`
- `set`
- `setex`
- `setnx`
- `setrange`
- `strlen`

## Hash

- `hdel`
- `hexists`
- `hget`
- `hgetall`
- `hincrby`
- `hincrbyfloat`
- `hkeys`
- `hlen`
- `hmget`
- `hmset`
- `hrandfield`
- `hscan`
- `hset`
- `hsetnx`
- `hstrlen`
- `hvals`

## List

- `blmove`
- `blpop`
- `brpop`
- `brpoplpush`
- `lindex`
- `linsert`
- `llen`
- `lmove`
- `lpop`
- `lpos`
- `lpush`
- `lpushx`
- `lrange`
- `lrem`
- `lset`
- `ltrim`
- `rpop`
- `rpoplpush`
- `rpush`
- `rpushx`

## Set

- `sadd`
- `scard`
- `sdiff`
- `sdiffstore`
- `sinter`
- `sinterstore`
- `sismember`
- `smembers`
- `smismember`
- `smove`
- `spop`
- `srandmember`
- `srem`
- `sscan`
- `sunion`
- `sunionstore`

## Sorted Set

- `bzpopmax`
- `bzpopmin`
- `zadd`
- `zcard`
- `zcount`
- `zdiff`
- `zdiffstore`
- `zincrby`
- `zinter`
- `zinterstore`
- `zlexcount`
- `zmscore`
- `zpopmax`
- `zpopmin`
- `zrandmember`
- `zrange`
- `zrangebylex`
- `zrangebyscore`
- `zrangestore`
- `zrank`
- `zrem`
- `zremrangebylex`
- `zremrangebyrank`
- `zremrangebyscore`
- `zrevrange`
- `zrevrangebylex`
- `zrevrangebyscore`
- `zrevrank`
- `zscan`
- `zscore`
- `zunion`
- `zunionstore`

## Stream

- `xack`
- `xadd`
- `xautoclaim`
- `xclaim`
- `xdel`
- `xgroup`
- `xinfo`
- `xlen`
- `xpending`
- `xrange`
- `xread`
- `xreadgroup`
- `xrevrange`
- `xsetid`
- `xtrim`

## HyperLogLog

- `pfadd`
- `pfcount`
- `pfmerge`

## Geo

- `geoadd`
- `geodist`
- `geohash`
- `geopos`
- `georadius`
- `georadiusbymember`
- `georadius_ro`
- `georadiusbymember_ro`
- `geosearch`
- `geosearchstore`

## Bitmap

- `bitcount`
- `bitfield`
- `bitfield_ro`
- `bitop`
- `bitpos`
- `getbit`
- `setbit`

## Pub/Sub

- `psubscribe`
- `publish`
- `pubsub`
- `punsubscribe`
- `subscribe`
- `unsubscribe`

## Transactions

- `discard`
- `exec`
- `multi`
- `unwatch`
- `watch`

## Scripting

- `eval`
- `evalsha`
- `script`

## Connection

- `auth`
- `client`
- `echo`
- `hello`
- `ping`
- `quit`
- `reset`
- `select`

## Key/Keyspace

- `copy`
- `del`
- `dump`
- `exists`
- `expire`
- `expireat`
- `keys`
- `migrate`
- `move`
- `object`
- `persist`
- `pexpire`
- `pexpireat`
- `pttl`
- `randomkey`
- `rename`
- `renamenx`
- `restore`
- `scan`
- `sort`
- `touch`
- `ttl`
- `type`
- `unlink`

## Server / Admin

- `acl`
- `bgrewriteaof`
- `bgsave`
- `command`
- `config`
- `dbsize`
- `debug`
- `failover`
- `flushall`
- `flushdb`
- `info`
- `lastsave`
- `latency`
- `lolwut`
- `memory`
- `module`
- `monitor`
- `psync`
- `replconf`
- `replicaof`
- `role`
- `save`
- `shutdown`
- `slaveof`
- `slowlog`
- `swapdb`
- `sync`
- `time`

## Cluster

- `asking`
- `cluster`
- `readonly`
- `readwrite`

## Wait

- `wait`

---

## Categories

For broader rules, use `type: category` with one of these names: `read`, `write`, `keyspace`, `string`, `hash`, `list`, `set`, `sortedset`, `stream`, `pubsub`, `admin`, `fast`, `slow`, `blocking`, `dangerous`, `connection`, `transaction`, `scripting`, `bitmap`, `hyperloglog`, `geo`, `all`.
