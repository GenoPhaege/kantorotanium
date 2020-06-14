# kantorotanium
Eve Online: optimize compressed ore purchases

Unlike other ore optimizers, this one never gives you "impossible" output by telling you to buy 10,000 units of something that has only 100 units available.
Each order on the market becomes its own constraint in the optimization problem.

## TODOs
* An actual user interface of any sort (right now you need to edit the source to provide problem input)
* When webapp-ifying, split the market order cache update into a cronjob, and also expose the last-update time in the webapp
* Allow multiple specifications of refining efficiency
* Support locations other than Jita 4-4 CNAP
* Re-evalaute the rounding (for cheaper ores, rounding to the nearest ISK is probably doing us a disservice)

## Sample output
    Yielding:
    1234526816x Tritanium (excess of 14402)
    100034466x Pyerite (excess of 132)
    1001231x Mexallon (excess of 1)
    601344x Isogen (excess of 912)
    500716x Noxcium (excess of 372)
    57516x Zydrine (excess of 26284)
    0x Megacyte (excess of 0)


    INPUT TO MULTIBUY:

    2068419x Compressed Concentrated Veldspar
    403430x Compressed Condensed Scordite
    455x Compressed Crokite
    661766x Compressed Dense Veldspar
    306832x Compressed Massive Scordite
    426x Compressed Onyx Ochre
    40x Compressed Pristine Jaspet
    3081x Compressed Pyroxeres
    49501x Compressed Scordite
    5477x Compressed Solid Pyroxeres
    540667x Compressed Veldspar
    17211x Compressed Viscous Pyroxeres
    1236x Compressed Vivid Hemorphite


    Total price: 14,850,373,413
