interface CacheRecord {
  value: unknown;
  expiresAt: number;
}

/**
 * Process-local TTL cache. Password-reset OTPs live here (key `pwdreset:{userId}`),
 * not in a table. Swap the implementation for Redis later without changing callers.
 */
class MemoryCache {
  private readonly store = new Map<string, CacheRecord>();

  get<T>(key: string): T | undefined {
    const record = this.store.get(key);
    if (record === undefined) {
      return undefined;
    }
    if (record.expiresAt <= Date.now()) {
      this.store.delete(key);
      return undefined;
    }
    return record.value as T;
  }

  set<T>(key: string, value: T, ttlMs: number): void {
    this.store.set(key, { value, expiresAt: Date.now() + ttlMs });
  }

  update<T>(key: string, next: T): boolean {
    const record = this.store.get(key);
    if (record === undefined || record.expiresAt <= Date.now()) {
      this.store.delete(key);
      return false;
    }
    record.value = next;
    return true;
  }

  delete(key: string): void {
    this.store.delete(key);
  }
}

export const cache = new MemoryCache();
