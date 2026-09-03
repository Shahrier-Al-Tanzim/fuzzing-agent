# Crash 55628614cd6c — stack-overflow@malloc

**Type:** `stack-overflow`
**Occurrences:** 32 input(s) mapped to this signature
**Verification:** crashed every run (3/3) but signature unstable (1/3 matched)

## Normalized stack (top 5 frames)

```
  #0  malloc
  #1  STRNDUP toml.c:85
  #2  normalize_key toml.c:681
  #3  create_keytable_in_table toml.c:782
  #4  parse_keyval toml.c:1132
```

Raw frames before normalization: 185
Consecutive identical frames collapsed: True

## Minimized reproducer

618893 bytes → 618893 bytes (0% smaller) via `delta-debugging` in 3 steps.

```toml
k0.k1.k2.k3.k4.k5.k6.k7.k8.k9.k10.k11.k12.k13.k14.k15.k16.k17.k18.k19.k20.k21.k22.k23.k24.k25.k26.k27.k28.k29.k30.k31.k32.k33.k34.k35.k36.k37.k38.k39.k40.k41.k42.k43.k44.k45.k46.k47.k48.k49.k50.k51.k52.k53.k54.k55.k56.k57.k58.k59.k60.k61.k62.k63.k64.k65.k66.k67.k68.k69.k70.k71.k72.k73.k74.k75.k76.k77.k78.k79.k80.k81.k82.k83.k84.k85.k86.k87.k88.k89.k90.k91.k92.k93.k94.k95.k96.k97.k98.k99.k100.k101.k102.k103.k104.k105.k106.k107.k108.k109.k110.k111.k112.k113.k114.k115.k116.k117.k118.k119.k120.k121.k122.k123.k124.k125.k126.k127.k128.k129.k130.k131.k132.k133.k134.k135.k136.k137.k138.k139.k140.k141.k142.k143.k144.k145.k146.k147.k148.k149.k150.k151.k152.k153.k154.k155.k156.k157.k158.k159.k160.k161.k162.k163.k164.k165.k166.k167.k168.k169.k170.k171.k172.k173.k174.k175.k176.k177.k178.k179.k180.k181.k182.k183.k184.k185.k186.k187.k188.k189.k190.k191.k192.k193.k194.k195.k196.k197.k198.k199.k200.k201.k202.k203.k204.k205.k206.k207.k208.k209.k210.k211.k212.k213.k214.k215.k216.k217.k218.k219.k220.k221.k222.k223.k224.k225.k226.k227.k228.k229.k230.k231.k232.k233.k234.k235.k236.k237.k238.k239.k240.k241.k242.k243.k244.k245.k246.k247.k248.k249.k250.k251.k252.k253.k254.k255.k256.k257.k258.k259.k260.k261.k262.k263.k264.k265.k266.k267.k268.k269.k270.k271.k272.k273.k274.k275.k276.k277.k278.k279.k280.k281.k282.k283.k284.k285.k286.k287.k288.k289.k290.k291.k292.k293.k294.k295.k296.k297.k298.k299.k300.k301.k302.k303.k304.k305.k306.k307.k308.k309.k310.k311.k312.k313.k314.k315.k316.k317.k318.k319.k320.k321.
... (truncated)
```

## Reproduce

```bash
source harness/sanitizer_env.sh
harness/build/toml_harness triage/reports/run_50/dotted_keys-55628614cd6c/minimized.toml
echo $?   # expect 86 (sanitizer) or a signal
```

## Deduplication choices applied

- Consecutive identical frames collapsed (recursion bugs otherwise report as
  many distinct bugs depending on where the stack ran out).
- Harness frames (`toml_harness`, sanitizer runtime, libc startup) excluded;
  bucketing uses library frames only.
- Frame identity is `function file:line`; addresses and absolute paths stripped.
