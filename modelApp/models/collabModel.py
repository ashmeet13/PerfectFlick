import torch


class CollabNN(torch.nn.Module):
    def __init__(self, num_users, num_items, emb_size):
        super(CollabNN, self).__init__()

        self.num_users = num_users
        self.num_items = num_items
        self.latent_dim = emb_size

        self.embedding_user = torch.nn.Embedding(
            num_embeddings=self.num_users,
            embedding_dim=self.latent_dim
            )

        self.embedding_item = torch.nn.Embedding(
            num_embeddings=self.num_items,
            embedding_dim=self.latent_dim
            )
        self.embedding_user.weight.data.fill_(0.01)
        self.embedding_item.weight.data.fill_(0.01)

        self.layers = [
            self.latent_dim*2,
            self.latent_dim**2,
            self.latent_dim*4,
            self.latent_dim
        ]

        self.fc_layers = torch.nn.ModuleList()
        
        for i in range(1, len(self.layers)):
            in_size = self.layers[i-1]
            out_size = self.layers[i]
            self.fc_layers.append(
                torch.nn.Linear(in_features=in_size, out_features=out_size)
                )

        self.affine_output = torch.nn.Linear(in_features=self.layers[-1], out_features=1)

    def forward(self, userIndex, movieIndex):
        user_embedding = self.embedding_user(userIndex)
        item_embedding = self.embedding_item(movieIndex)
        vector = torch.cat([user_embedding, item_embedding], dim=-1)
        for idx, _ in enumerate(range(len(self.fc_layers))):
            vector = self.fc_layers[idx](vector)
            vector = torch.nn.ReLU()(vector)
        rating = self.affine_output(vector)
        return rating

    def getModelInfo(self):
        return {
            "Users" : self.num_users,
            "Items" : self.num_items,
            "Embed" : self.latent_dim
        }
