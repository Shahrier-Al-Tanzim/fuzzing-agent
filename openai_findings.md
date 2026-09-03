## Run 40

=== iteration 3/4
==============================================================
  refining previous strategy from feedback...
    attempt 1: FAIL acceptance (11413 tok, 11.45s)
    attempt 2: FAIL imports (11400 tok, 7.77s)
    attempt 3: FAIL acceptance (11359 tok, 9.26s)
    attempt 4: FAIL imports (11510 tok, 10.01s)
    attempt 5: FAIL draw (11343 tok, 8.59s)
    attempt 6: FAIL imports (11408 tok, 9.82s)
    attempt 7: PASS (11453 tok, 10.0s)
  running up to 500 examples...


!! Unexpected error: AttributeError: 'int' object has no attribute 'map'
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/tanzim/fuzzing-agent/agent/loop.py", line 361, in <module>
    sys.exit(main())
             ~~~~^^
  File "/home/tanzim/fuzzing-agent/agent/loop.py", line 266, in main
    records, novel = run_iteration(iteration, strategy, state)
                     ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/tanzim/fuzzing-agent/agent/loop.py", line 136, in run_iteration
    check()
    ~~~~~^^
  File "/home/tanzim/fuzzing-agent/agent/loop.py", line 115, in check
    @settings(
           ^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/core.py", line 1722, in wrapped_test
    raise the_error_hypothesis_found
  File "<iter_03_strategy>", line 79, in document
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/internal/conjecture/data.py", line 2519, in draw
    return strategy.do_draw(self)
           ~~~~~~~~~~~~~~~~^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/strategies/_internal/lazy.py", line 167, in do_draw
    return data.draw(self.wrapped_strategy)
           ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/internal/conjecture/data.py", line 2519, in draw
    return strategy.do_draw(self)
           ~~~~~~~~~~~~~~~~^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/strategies/_internal/collections.py", line 195, in do_draw
    result.append(data.draw(self.element_strategy))
                  ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/internal/conjecture/data.py", line 2519, in draw
    return strategy.do_draw(self)
           ~~~~~~~~~~~~~~~~^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/strategies/_internal/strategies.py", line 682, in do_draw
    return data.draw(strategy)
           ~~~~~~~~~^^^^^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/internal/conjecture/data.py", line 2519, in draw
    return strategy.do_draw(self)
           ~~~~~~~~~~~~~~~~^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/strategies/_internal/lazy.py", line 167, in do_draw
    return data.draw(self.wrapped_strategy)
           ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/internal/conjecture/data.py", line 2519, in draw
    return strategy.do_draw(self)
           ~~~~~~~~~~~~~~~~^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/strategies/_internal/core.py", line 1785, in do_draw
    return self.definition(data.draw, *self.args, **self.kwargs)
           ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<iter_03_strategy>", line 69, in pair
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/internal/conjecture/data.py", line 2519, in draw
    return strategy.do_draw(self)
           ~~~~~~~~~~~~~~~~^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/strategies/_internal/lazy.py", line 167, in do_draw
    return data.draw(self.wrapped_strategy)
           ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/internal/conjecture/data.py", line 2519, in draw
    return strategy.do_draw(self)
           ~~~~~~~~~~~~~~~~^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/strategies/_internal/core.py", line 1785, in do_draw
    return self.definition(data.draw, *self.args, **self.kwargs)
           ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<iter_03_strategy>", line 42, in value
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/internal/conjecture/data.py", line 2519, in draw
    return strategy.do_draw(self)
           ~~~~~~~~~~~~~~~~^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/strategies/_internal/strategies.py", line 682, in do_draw
    return data.draw(strategy)
           ~~~~~~~~~^^^^^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/internal/conjecture/data.py", line 2519, in draw
    return strategy.do_draw(self)
           ~~~~~~~~~~~~~~~~^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/strategies/_internal/lazy.py", line 167, in do_draw
    return data.draw(self.wrapped_strategy)
           ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/internal/conjecture/data.py", line 2519, in draw
    return strategy.do_draw(self)
           ~~~~~~~~~~~~~~~~^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/strategies/_internal/core.py", line 1785, in do_draw
    return self.definition(data.draw, *self.args, **self.kwargs)
           ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<iter_03_strategy>", line 26, in unicode_escape
AttributeError: 'int' object has no attribute 'map'
while generating 'text' from one_of(document(), document(), document(), document(), document(), document(), document(), document(), document(), document(), document(), document(), document(), document(), document(), document(), document(), document(), document(), document(), deep_array(), deep_inline_table(), deep_dotted_key(), deep_mixed_nesting(), deep_quoted_mixed(), many_siblings())?



but next run it works


41
=============================================================
=== iteration 0/4
==============================================================
  generating seed strategy from grammar...
    attempt 1: FAIL syntax (9873 tok, 7.17s)
    attempt 2: FAIL imports (10181 tok, 8.47s)
    attempt 3: FAIL draw (9925 tok, 8.03s)
    attempt 4: FAIL draw (9984 tok, 6.42s)
    attempt 5: FAIL syntax (25693 tok, 136.09s)
    attempt 6: FAIL imports (10078 tok, 7.86s)
    attempt 7: FAIL draw (10103 tok, 6.94s)
    attempt 8: FAIL imports (10000 tok, 12.23s)
  !! generation failed; reusing previous strategy
  !! no previous strategy to fall back on - stopping
(.venv) tanzim@LAPTOP-NDPF1SP8:~/fuzzing-agent$ python -m agent.loop --resume
Provider: OpenAI (remote)
Run: 41

==============================================================
=== iteration 0/4
==============================================================
  generating seed strategy from grammar...
    attempt 1: FAIL imports (9879 tok, 6.79s)
    attempt 2: FAIL draw (9797 tok, 6.21s)
    attempt 3: FAIL imports (9913 tok, 6.28s)
    attempt 4: FAIL draw (9763 tok, 4.57s)
    attempt 5: FAIL imports (9776 tok, 4.71s)
    attempt 6: FAIL draw (9760 tok, 4.44s)
    attempt 7: PASS (10191 tok, 7.89s)
  running up to 500 examples...


!! Unexpected error: TypeError: sequence item 0: expected str instance, int found
Traceback (most recent call last):
  File "<frozen runpy>", line 198, in _run_module_as_main
  File "<frozen runpy>", line 88, in _run_code
  File "/home/tanzim/fuzzing-agent/agent/loop.py", line 361, in <module>
    sys.exit(main())
             ~~~~^^
  File "/home/tanzim/fuzzing-agent/agent/loop.py", line 266, in main
    records, novel = run_iteration(iteration, strategy, state)
                     ~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/tanzim/fuzzing-agent/agent/loop.py", line 136, in run_iteration
    check()
    ~~~~~^^
  File "/home/tanzim/fuzzing-agent/agent/loop.py", line 115, in check
    @settings(
           ^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/core.py", line 1722, in wrapped_test
    raise the_error_hypothesis_found
  File "<iter_00_strategy>", line 41, in document
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/internal/conjecture/data.py", line 2519, in draw
    return strategy.do_draw(self)
           ~~~~~~~~~~~~~~~~^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/strategies/_internal/lazy.py", line 167, in do_draw
    return data.draw(self.wrapped_strategy)
           ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/internal/conjecture/data.py", line 2519, in draw
    return strategy.do_draw(self)
           ~~~~~~~~~~~~~~~~^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/strategies/_internal/collections.py", line 195, in do_draw
    result.append(data.draw(self.element_strategy))
                  ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/internal/conjecture/data.py", line 2519, in draw
    return strategy.do_draw(self)
           ~~~~~~~~~~~~~~~~^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/strategies/_internal/strategies.py", line 682, in do_draw
    return data.draw(strategy)
           ~~~~~~~~~^^^^^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/internal/conjecture/data.py", line 2519, in draw
    return strategy.do_draw(self)
           ~~~~~~~~~~~~~~~~^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/strategies/_internal/lazy.py", line 167, in do_draw
    return data.draw(self.wrapped_strategy)
           ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/internal/conjecture/data.py", line 2519, in draw
    return strategy.do_draw(self)
           ~~~~~~~~~~~~~~~~^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/strategies/_internal/core.py", line 1785, in do_draw
    return self.definition(data.draw, *self.args, **self.kwargs)
           ~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "<iter_00_strategy>", line 32, in key_value
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/internal/conjecture/data.py", line 2519, in draw
    return strategy.do_draw(self)
           ~~~~~~~~~~~~~~~~^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/strategies/_internal/strategies.py", line 682, in do_draw
    return data.draw(strategy)
           ~~~~~~~~~^^^^^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/internal/conjecture/data.py", line 2519, in draw
    return strategy.do_draw(self)
           ~~~~~~~~~~~~~~~~^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/strategies/_internal/recursive.py", line 112, in do_draw
    return data.draw(self.strategy)
           ~~~~~~~~~^^^^^^^^^^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/internal/conjecture/data.py", line 2519, in draw
    return strategy.do_draw(self)
           ~~~~~~~~~~~~~~~~^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/strategies/_internal/strategies.py", line 682, in do_draw
    return data.draw(strategy)
           ~~~~~~~~~^^^^^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/internal/conjecture/data.py", line 2519, in draw
    return strategy.do_draw(self)
           ~~~~~~~~~~~~~~~~^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/strategies/_internal/lazy.py", line 167, in do_draw
    return data.draw(self.wrapped_strategy)
           ~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/internal/conjecture/data.py", line 2519, in draw
    return strategy.do_draw(self)
           ~~~~~~~~~~~~~~~~^^^^^^
  File "/home/tanzim/fuzzing-agent/.venv/lib/python3.14/site-packages/hypothesis/strategies/_internal/strategies.py", line 844, in do_draw
    result = self.pack(x)  # type: ignore
  File "<iter_00_strategy>", line 18, in <lambda>
TypeError: sequence item 0: expected str instance, int found
while generating 'text' from one_of(document(), document(), document(), document(), document(), document(), document(), document(), document(), document(), document(), document(), document(), document(), document(), document(), document(), document(), document(), document(), deep_array(), deep_inline_table(), many_siblings())
