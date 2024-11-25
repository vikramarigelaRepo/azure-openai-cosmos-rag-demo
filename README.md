# Implement RAG with Azure Cosmos db as VectorStore
Repo that explains how to enable vector store features in Azure cosmos db and implement
a simple RAG app using Azure Open AI and Azure Cosmos Db as vector store.

# Enabling Vector Store capabilities in Azure Cosmos db
Let us see how to enable vector search in Azure cosmos db. For Complete details please check go through link 
https://learn.microsoft.com/en-us/azure/cosmos-db/nosql/vector-search
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

    ![image](https://github.com/user-attachments/assets/431db8af-2f38-4a75-a8f3-57754301cbd1)

    ![image](https://github.com/user-attachments/assets/c1fb5164-da6b-433a-94ef-d858cab89916)

  * Vector Indexing Policies
    Vector indexes increase the efficiency when performing vector searches using the VectorDistance system function. Vectors searches have lower latency, higher throughput, 
    and less RU consumption when using a vector index. You can specify the following types of vector index policies:

    ![image](https://github.com/user-attachments/assets/ef812134-e02b-4ab4-a114-fbb9b05b7ea1)

    Example of valid vector indexing policy

   ![image](https://github.com/user-attachments/assets/9712e0d1-3921-4fd6-b69f-9c057a2b06d8)

   ![image](https://github.com/user-attachments/assets/8960d63c-95b3-4b45-94d1-5eb292d7552b)





    

