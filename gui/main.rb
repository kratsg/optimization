require 'open3'
require 'pry'

Shoes.app width: 800, title: "Optimization" do
    background "#000"
    stack do
        background "#000"
        title "Optimization.. for the rest of us", :align => 'center', stroke: "#FFF"
    end
    stack width: 200, height: 40, margin_left: 50 do
        background "#DFA"
        para "Step 1"
    end
    stack width: -200 do
        background "#DF0"
        flow do
            button "Pick your supercuts file" do
                @configurations_file.text = ask_open_file
            end
            @configurations_file = para
        end
    end
    stack width: 200, height: 400, margin_left: 50 do
        background "#D0A"
        para "Step 2"
    end
    stack width: -200 do
        background "#D00"
        subtitle "Foo"
        button do
            binding.pry
            stdout, stderr, status = Open3.capture3("python ../optimize.py -h")
            @log.text = stderr
        end
        @log = para
    end
    para "Hello World", stroke: "#00FFFF"
end
