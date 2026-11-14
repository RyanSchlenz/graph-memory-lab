# measures memory with fields removed, so will need to load the file, record current memory, delete columns from every node, then record current memory again. It would delete joinCondition from every node, then records again. What is left is the light part of each node, id, name, nodeType, dependencies. Record the results. 

# start tracking memory
# open graph.json and parse it into a list of nodes
# record current memory as before


# delete columns from every node
# clean up leftover garbage with gc.collect()
# record current memory as after_columns


# delete joinCondition from every node
# clean up leftover garbage with gc.collect()
# record current memory as after_sql


# print one node to check that only id, name, nodeType, and dependencies are left
# calculate the columns, SQL, and light-part percents, each out of before
# print the three percentages