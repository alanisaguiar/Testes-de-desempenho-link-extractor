#!/usr/bin/env ruby
# encoding: utf-8

require "sinatra"
require "open-uri"
require "uri"
require "nokogiri"
require "json"

set :protection, :except=>:path_traversal

get "/" do
  "Usage: http://<hostname>[:<prt>]/api/<url>"
end

get "/api/*" do
  url = [params['splat'].first, request.query_string].reject(&:empty?).join("?")

  # SEM CACHE:
  # Sempre extrai os links diretamente da URL,
  # sem consultar nem salvar no Redis.
  jsonlinks = JSON.pretty_generate(extract_links(url))

  status 200
  headers "content-type" => "application/json"
  body jsonlinks
end

def extract_links(url)
  links = []
  doc = Nokogiri::HTML(open(url))

  doc.css("a").each do |link|
    text = link.text.strip.split.join(" ")

    begin
      links.push({
        text: text.empty? ? "[IMG]" : text,
        href: URI.join(url, link["href"])
      })
    rescue
    end
  end

  links
end