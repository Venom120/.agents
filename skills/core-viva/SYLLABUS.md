# Core subjects syllabus

The topics that come up in technical placement rounds, roughly ordered by how often they're asked.

## Operating Systems
- Process vs thread; process states and the PCB; context switching
- CPU scheduling: FCFS, SJF/SRTF, Round Robin, Priority (with numericals: waiting/turnaround time)
- Synchronization: race conditions, critical section, mutex vs semaphore, monitors, producer-consumer, readers-writers, dining philosophers
- Deadlock: Coffman conditions, prevention vs avoidance (Banker's algorithm) vs detection
- Memory: paging, segmentation, TLB, page tables, virtual memory, demand paging, thrashing
- Page replacement: FIFO, LRU, Optimal (numericals), Belady's anomaly
- Fragmentation (internal vs external); user vs kernel mode; system calls; fork/exec
- IPC: pipes, shared memory, message queues; starvation and aging

## DBMS
- Keys: primary, candidate, super, foreign, composite
- Normalization: 1NF, 2NF, 3NF, BCNF, functional dependencies, anomalies
- ACID; transactions; isolation levels; dirty/non-repeatable/phantom reads
- Concurrency control: 2PL, timestamp ordering, deadlocks in DBs
- Indexing: B/B+ trees, clustered vs non-clustered, when indexes hurt
- ER model, relational algebra basics
- SQL vs NoSQL; CAP theorem; sharding vs replication
- Views, stored procedures, triggers

## Computer Networks
- OSI vs TCP/IP model, and what each layer does
- TCP vs UDP; three-way handshake; four-way teardown; flow vs congestion control
- What happens when you type a URL into a browser (DNS, TCP, TLS, HTTP, rendering)
- HTTP methods, status codes, HTTP/1.1 vs HTTP/2 vs HTTP/3, cookies vs sessions vs tokens
- DNS resolution; DHCP; ARP; NAT
- IP addressing, subnetting and CIDR (numericals), IPv4 vs IPv6
- HTTPS/TLS handshake basics, symmetric vs asymmetric encryption
- Sockets; load balancers; proxies vs reverse proxies; CDN

## OOP
- Four pillars: encapsulation, abstraction, inheritance, polymorphism (with code examples)
- Compile-time vs runtime polymorphism; overloading vs overriding
- Abstract class vs interface; multiple inheritance and the diamond problem
- Constructors/destructors, copy constructor, shallow vs deep copy
- Access modifiers; static vs instance; `this`/`super`
- SOLID principles; composition vs inheritance
- Common design patterns: Singleton, Factory, Observer, Strategy
- Language-specific: virtual functions and vtables (C++), `final`/`equals`/`hashCode` (Java), dunder methods (Python)

## SQL (asked as runnable queries)
- SELECT with WHERE, ORDER BY, LIMIT; DISTINCT
- JOINs: inner, left, right, full, self, cross
- GROUP BY with HAVING; aggregates
- Subqueries, correlated subqueries, EXISTS vs IN
- Nth highest salary (several ways); finding and deleting duplicates
- Window functions: ROW_NUMBER, RANK, DENSE_RANK, LAG/LEAD, running totals
- NULL semantics; CASE expressions; UNION vs UNION ALL
- DELETE vs TRUNCATE vs DROP; indexes and EXPLAIN basics

## Bonus (only if asked)
- Git: merge vs rebase, reset vs revert, resolving conflicts
- Linux: processes, permissions, pipes, grep/awk basics
- Compilers/COA basics for core-heavy rounds
