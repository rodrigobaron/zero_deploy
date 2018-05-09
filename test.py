import zero_deploy

with zero_deploy.env(servers='local', use_env=True) as env:
    conn = env.connect()
    np = conn.modules.numpy
    tf = conn.modules.tensorflow
    input_data = conn.modules['tensorflow.examples.tutorials.mnist'].input_data
    mnist = input_data.read_data_sets("/tmp/MNIST_data/", one_hot=True)

    x = tf.placeholder(tf.float32, [None, 784])
    W = tf.Variable(tf.zeros([784, 10]))
    b = tf.Variable(tf.zeros([10]))

    y = tf.nn.softmax(tf.matmul(x, W) + b)

    y_ = tf.placeholder(tf.float32, [None, 10])
    cross_entropy = tf.reduce_mean(-tf.reduce_sum(y_ * tf.log(y), reduction_indices=[1]))
    train_step = tf.train.GradientDescentOptimizer(0.5).minimize(cross_entropy)

    init = tf.global_variables_initializer()

    saver = tf.train.Saver()
    sess = tf.Session()
    sess.run(init)
    for e in range(20):
        if conn.modules.os.path.exists("/tmp/model.ckpt"):
            saver.restore(sess, "/tmp/model.ckpt")
        for i in range(10):
            batch_xs, batch_ys = mnist.train.next_batch(100)
            sess.run(train_step, feed_dict={x: batch_xs, y_: batch_ys})
            if i % 10 == 0:
                correct_prediction = tf.equal(tf.argmax(y,1), tf.argmax(y_,1))
                accuracy = tf.reduce_mean(tf.cast(correct_prediction, tf.float32))
                zero_deploy.remote_print(conn, "{0:3d} times\taccuracy: {1:.10f} %".format(i+100, sess.run(accuracy, feed_dict={x: mnist.test.images, y_: mnist.test.labels})*100))
            save_path = saver.save(sess, "/tmp/model.ckpt")