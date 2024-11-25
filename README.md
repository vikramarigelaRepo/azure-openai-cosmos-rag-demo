# Implement RAG with Azure Cosmos db as VectorStore
Repo that explains how to enable vector store features in Azure cosmos db and implement
a simple RAG app using Azure Open AI and Azure Cosmos Db as vector store.

# Enabling Vector Store capabilities in Azure Cosmos db
Let us see how to enable vector search in Azure cosmos db
  * Enable feature Vector Search for NoSQL API under features
    ![image](https://github.com/user-attachments/assets/5661f958-73b6-450e-9fb0-ab34d2895ca3)

  * Container Vector Policies :
     Performing vector search with Azure Cosmos DB for NoSQL requires you to define a vector policy for the container. This 
     provides essential information for the database 
     engine to conduct efficient similarity search for vectors found in the container's documents. This also informs the 
     vector indexing policy of necessary information,  should you choose to specify one. The following information is 
     included in the contained vector policy:

      * “path”: the property containing the vector (required).
      * “datatype”: the data type of the vector property (default Float32). 
      * “dimensions”: The dimensionality or length of each vector in the path. All vectors in a path should have the same  
        number of dimensions. (default 1536).
      * “distanceFunction”: The metric used to compute distance/similarity. Supported metrics are:
         cosine, which has values from -1 (least similar) to +1 (most similar).
         dot product, which has values from -inf (least similar) to +inf (most similar).
         euclidean, which has values from 0 (most similar) to +inf) (least similar).
       
  * Policy with Single Vector Path
     * {
          "vectorEmbeddings": [
              {
                  "path":"/vector1",
                  "dataType":"float32",
                  "distanceFunction":"cosine",
                  "dimensions":1536
              }
          ]
      }

    ![image](https://github.com/user-attachments/assets/c1fb5164-da6b-433a-94ef-d858cab89916)

    

