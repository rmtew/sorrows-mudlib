#stacklesslib.locks.py
#See the LICENSE file for copyright information.
"""
This module provides locking primitives to be used with stackless.
The primitives have the same semantics as those defined in the threading module
for threads.
The timeout feature of the locks works only if someone is pumping the stacklesslib.main.event_queue
"""

from __future__ import with_statement
from __future__ import absolute_import
import stackless
from .main import set_channel_pref, event_queue, elapsed_time
from .util import atomic

class LockTimeoutError(RuntimeError):
    pass

def channel_wait(chan, timeout):
    if timeout is None:
        chan.receive()
        return True
        
    waiting_tasklet = stackless.getcurrent()
    def break_wait():
        #careful to only timeout if it is still blocked.  This ensures
        #that a successful channel.send doesn't simultaneously result in
        #a timeout, which would be a terrible source of race conditions.
        with atomic():
            if waiting_tasklet and waiting_tasklet.blocked:
                waiting_tasklet.raise_exception(LockTimeoutError)
    with atomic():
        try:
            #schedule the break event after a certain time
            event_queue.push_after(break_wait, timeout)
            chan.receive()
            return True
        except LockTimeoutError:
            return False
        finally:
            waiting_tasklet = None
            
class LockMixin(object):
    def __enter__(self):
        self.acquire()    
    def __exit__(self, exc, val, tb):
        self.release()            
            
class Lock(LockMixin):
    def __init__(self):
        self.channel = stackless.channel()
        set_channel_pref(self.channel)
        self.owning = None
        
    def acquire(self, blocking=True, timeout=None):
        with atomic():
            got_it = self._try_acquire()
            if got_it or not blocking:
                return got_it
            
            wait_until = None
            while True:
                if timeout is not None:
                    #adjust time.  We may have multiple wakeups since we are a low-contention lock.
                    if wait_until is None:
                        wait_until = elapsed_time() + timeout                        
                    else:
                        timeout = wait_until - elapsed_time()
                        if timeout < 0:
                            return False
                try:
                    channel_wait(self.channel, timeout)                    
                except:
                    self._safe_pump()
                    raise
                if self._try_acquire():
                    return True
                            
    def _try_acquire(self):
        if self.owning is None:
            self.owning = stackless.getcurrent()
            return True
        return False
       
    def release(self):
        with atomic():
            self.owning = None
            self._pump()
        
    def _pump(self):
        if not self.owning and self.channel.balance:
            self.channel.send(None)
    
    def _safe_pump(self):
        #need a special function for this, since we want to call it from
        #an exception handler and not trample the current exception in case
        #we get one ourselves.
        try:
            self._pump()
        except Exception:
            pass
            
class RLock(Lock):
    def __init__(self):
        Lock.__init__(self)
        self.recursion = 0
        
    def _try_acquire(self):
        if self.owning is None or self.owning is stackless.getcurrent():
            self.owning = stackless.getcurrent()
            self.recursion += 1
            return True
        return False
        
    def release(self):
        if self.owning is not stackless.getcurrent():
            raise RuntimeError("cannot release un-aquired lock")
        with atomic():
            self.recursion -= 1
            if not self.recursion:
                self.owning = None
                self._pump()
    
    #These three functions form an internal interface for the Condition.
    #It allows the Condition instances to release the lock from any
    #recursion level and reaquire it to the same level.
    def _is_owned(self):
        return self.owning is stackless.getcurrent()
    
    def _release_save(self):
        r = self.owning, self.recursion
        self.owning, self.recursion = None, 0
        self._pump()
        return r
        
    def _acquire_restore(self, r):
        self.acquire()
        self.owning, self.recursion = r

class Condition(LockMixin):
    def __init__(self, lock=None):
        if not lock:
            lock = RLock()
        self.lock = lock
        #We impolement the condition using the Semaphore, because the Semaphore embodies
        #the non-blocking send, required to resolve the race condition which would otherwise
        #exist WRT timeouts and the nWaiting bookkeeping.
        self.sem = Semaphore(0)
        #we need bookkeeping to avoid the "missing wakeup" bug.
        self.nWaiting = 0
        
        # Export the lock's acquire() and release() methods
        self.acquire = lock.acquire
        self.release = lock.release
        # If the lock defines _release_save() and/or _acquire_restore(),
        # these override the default implementations (which just call
        # release() and acquire() on the lock).  Ditto for _is_owned().
        try:
            self._release_save = lock._release_save
            self._acquire_restore = lock._acquire_restore
            self._is_owned = lock._is_owned
        except AttributeError:
            pass

    def _release_save(self):
        self.lock.release()           # No state to save

    def _acquire_restore(self, x):
        self.lock.acquire()           # Ignore saved state    
    
    def _is_owned(self):
        if self.lock.acquire(False):
            self.lock.release()
            return True
        else:
            return False
    
    def wait(self, timeout=None):
        if not self._is_owned():
            raise RuntimeError("cannot wait on un-aquired lock")
        #to avoid a "missed wakeup" we need this bookkeeping before calling _release_save()
        c = stackless.getcurrent()
        self.nWaiting += 1
        saved = self._release_save()
        try:
            got_it = self.sem.acquire(timeout=timeout)
            if not got_it:
                self.nWaiting -= 1              
        finally:
            self._acquire_restore(saved)
        return got_it
        
    def wait_for(self, predicate, timeout=None):
        """
        Wait until a predicate becomes true, or until an optional timeout elapses.
        Returns the last value of the predicate.
        """
        result = predicate()
        if result:
            return result
        endtime = None
        while not result:
            if timeout is not None:
                if endtime is None:
                    endtime = elapsed_time() + timeout
                else:
                    timeout = endtime - elapsed_time()
                    if timeout < 0:
                        return result #a timeout occurred
            result = self.wait(timeout)
        return result
                
    def notify(self, n=1):
        if not self._is_owned():
            raise RuntimeError("cannot notify on un-aquired lock")
        n = min(n, self.nWaiting)
        if n > 0:
            self.nWaiting -= n
            self.sem.release(n)            
            
    def notify_all(self):
        self.notify(self.nWaiting)
    notifyAll = notify_all
    

class Semaphore(LockMixin):
    def __init__(self, value=1):
        if value < 0:
            raise ValueError
        self._value = value
        self._chan = stackless.channel()
        set_channel_pref(self._chan)
        
    def acquire(self, blocking=True, timeout=None):
        with atomic():
            if self._value > 0:
                self._value -= 1;
                return True
            if not blocking:
                return False
            return channel_wait(self._chan, timeout)
            
    def release(self, count=1):
        with atomic():
            for i in xrange(count):
                if self._chan.balance:
                    assert self._value == 0
                    self._chan.send(None)
                else:
                    self._value += 1

class BoundedSemaphore(Semaphore):
    def __init__(self, value=1):
        Semaphore.__init__(self, value)
        self._max_value = value
        
    def release(self, count=1):
        with atomic():
            for i in xrange(count):
                if self._chan.balance:
                    assert self._value == 0
                    self._chan.send(None)
                else:
                    if self._value == self._max_value:
                        raise ValueError
                    self._value += 1

class Event(object):
    def __init__(self):
        self._is_set = False
        self.chan = stackless.channel()
        set_channel_pref(self.chan)
        
    def is_set(self):
        return self._is_set;
    isSet = is_set
    
    def clear(self):
        self._is_set = False
        
    def wait(self, timeout=None):
        with atomic():
            if self._is_set:
                return True
            channel_wait(self.chan, timeout)
            return self._is_set
            
    def set(self):
        self._is_set = True
        for i in range(-self.chan.balance):
            self.chan.send(None)

